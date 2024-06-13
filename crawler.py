import json
import time
import urllib
import calendar
import gzip
from urllib.request import Request, urlopen
import os
import datetime
from github import Github
from github import RateLimitExceededException
import traceback
import pymysql
import re
import requests
import jpype
from nltk.tokenize import word_tokenize

# the token of GitHub User, meant to crawl the GitHub API
g = Github("GitHub Access Token")

code_related_words_list = ['code', 'program']
simplify_key_words_list = ['simplify', 'simplification', 'shorten', 'reduce', 'reduction', 'refactor', 'refactoring']
simplify_anti_words_list = ['config', 'fix', 'bug', 'patch', 'merge', 'misspelling', 'typo', 'warning', 'comment', 'doc']

unzip_file_path = 'unzipfiles/'
filter_file_path = 'filterfiles/'
baseURL = "https://data.gharchive.org/"

filter_commits_dict = {}

filter_commits_dict_file_name = 'total_filtered_commits.json'

def start_jvm():
    # JVM path, link to the jvm.dll
    jvmPath = "JVM path"
    # the dependency jar path
    ext_classpath = "denpendency jar path"
    # if JVM already started
    if not jpype.isJVMStarted():
        jpype.startJVM(jvmPath, "-ea", "-Djava.class.path=%s" % ext_classpath)


def shut_jvm():
    # shut down JVM
    if jpype.isJVMStarted():
        jpype.shutdownJVM()



def create_java_file(filePath, fileName, fileContent):
    try:
        full_path = filePath + fileName
        file = open(full_path, 'w+', encoding='utf-8')
        if str(fileContent) == 'nan':
            to_str = ''
        else:
            to_str = str(fileContent)
        file.write(to_str)
        file.close()
        return True
    except Exception as ex:
        traceback.print_exc()
        return False


def delete_java_file(filePath, fileName):
    try:
        full_path = filePath + fileName
        if os.path.exists(full_path):
            os.remove(full_path)
        else:
            return False
        return True
    except Exception as ex:
        return False


def db_query(query_sql):
    db = pymysql.connect(host="127.0.0.1", user="username", password="password", db="crawled_data", port=3306)
    cursor = db.cursor()
    retrieved_list = []
    try:
        cursor.execute(query_sql)
        results = cursor.fetchall()
        for row in results:
            retrieved_list.append(list(row))
    except:
        traceback.print_exc()
        print("Error: unable to fetch data")
    db.close()
    # print(retrieved_list)
    print('len of retrieved_list is: ', len(retrieved_list))
    return retrieved_list

# query_sql = "SELECT * FROM github_simplified_commit"
# db_query(query_sql)

def update_row(update_sql, update_args):
    db = pymysql.connect(host="127.0.0.1", user="username", password="password", db="crawled_data", port=3306)
    cursor = db.cursor()
    try:
        cursor.executemany(update_sql, update_args)
        db.commit()
        effectedRows = cursor.rowcount
        print('---update effectedRows---', effectedRows)
    except:
        traceback.print_exc()
        db.rollcack()

    db.close()

# update_args = [('0', '0', '3cfa9bbcf2920cf174c5b68c4fd2b7429da3f589')]
# update_sql = "UPDATE github_simplified_commit SET is_crawled = %s and is_real = %s WHERE sha = %s"
# update_row(update_sql, update_args)

def insert_rows(sql, insert_data):
    db = pymysql.connect(host="127.0.0.1", user="username", password="password", db="crawled_data", port=3306)
    cursor = db.cursor()

    try:
        cursor.executemany(sql, insert_data)
        db.commit()
        effectedRows = cursor.rowcount
        print(effectedRows)
    except:
        traceback.print_exc()
        db.rollback()

    cursor.close()
    db.close()

# insert_rows()

def read_json_file_by_lines(json_file_path):
    json_list = []
    with open(json_file_path, encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            try:
                js = json.loads(str(line))
                json_list.append(js)
            except Exception:
                print('!!!!!!!!!!!!!!!there are exceptions when load json string from json file, great chance the format of json string is wrong!')
                traceback.print_exc()
                continue
    return json_list


def check_if_str_in_list(target_list, obj_str):
    for target_str in target_list:
        if str(target_str) in str(obj_str).lower():
            return True
    return False


def check_if_commit_message_is_simplification_related(raw_commit_message):
    '''
    if commit message contains code or program, and contain simplify-related keywords, not contain simplify anti-words, then return true
    '''
    if check_if_str_in_list(code_related_words_list, raw_commit_message) and check_if_str_in_list(simplify_key_words_list, raw_commit_message) and (not check_if_str_in_list(simplify_anti_words_list, raw_commit_message)):
        return True

    return False


def remove_json_file(json_file_path):
    if os.path.exists(json_file_path):
        os.remove(json_file_path)
        print('--remove file--', json_file_path)
    else:
        print("The file does not exist")

def write_filter_commits_into_txt(file_path, data_list):
    with open(file_path, 'w', encoding='utf-8') as f:
        for commit_data in data_list:
            f.write(json.dumps(commit_data))
            f.write('\n')
    f.close()
    print(file_path, ' write_filtered_commits_into_txt files written.')

# target_file_path = 'test/a.json'
# write_filter_commits_into_txt(target_file_path, [])

def load_filter_commits_dict_from_txt(total_filter_dict_file_path):
    filter_commits_dict.clear()
    filter_json_list = read_json_file_by_lines(total_filter_dict_file_path)
    for one_json in filter_json_list:
        commit_sha = one_json['sha']
        filter_commits_dict[commit_sha] = one_json

def filter_json_by_commit_message(json_file_path):
    json_list = read_json_file_by_lines(json_file_path)
    for i in range(len(json_list)):
        json_str_dict = json_list[i]
        event_type = json_str_dict['type']
        if event_type == 'PushEvent':
            '''
            One or more commits are pushed to a repository branch or tag.
            '''
            if 'payload' in json_str_dict.keys():
                if 'commits' in json_str_dict['payload'].keys():
                    commits_list = json_str_dict['payload']['commits']
                    for commit in commits_list:
                        commit_message = str(commit['message'])
                        commit_sha = str(commit['sha'])
                        if check_if_commit_message_is_simplification_related(commit_message):
                            if commit_sha not in filter_commits_dict.keys():
                                filter_commits_dict[commit_sha] = commit
                            # else:
                            #     print("this commit_sha is already in the dict!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            #     print(commit_sha)
                            #     print(commit)
    print('current filtered commits count is: ', len(filter_commits_dict.values()))
    remove_json_file(json_file_path)



def download_gzfile_and_unzip(zip_file_url, target_file_path):
    print('--start download--', zip_file_url)
    delay = 5
    max_retries = 7
    # for _ in range(max_retries):
    try:
        req = Request(
            url=zip_file_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        webpage = urlopen(req).read()
        # break
        with open(target_file_path, 'wb') as outfile:
            outfile.write(gzip.decompress(webpage))
        print('--unzip --', target_file_path)
    except urllib.error.URLError:
        print('exception occurs when download things')
        traceback.print_exc()
        # time.sleep(delay)
        # delay *= 2
        write_filter_commits_into_txt(target_file_path, [])



def get_total_days_list(total_days):
    days_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09']
    i = 10
    while i <= total_days:
        days_list.append(str(i))
        i = i + 1
    return days_list

def get_total_day_of_month(year, month):
    if month in ['01', '03', '05', '07', '08', '10', '12']:
        total_days = 31
    elif month in ['04', '06', '09', '11']:
        total_days = 30
    else:
        if (int(year) % 4 == 0 and int(year) % 100 != 0) or (int(year) % 400 == 0):
            total_days = 29
        else:
            total_days = 28
    return total_days


def load_information_from_database_and_download_daily_event(current_line, total_zip_info_list):
    current_zip_file_information = total_zip_info_list[current_line]
    zip_file_url = current_zip_file_information[0]
    unzip_file_name = current_zip_file_information[1]
    zip_file_is_downloaded = current_zip_file_information[2]

    is_download = '1'
    update_commit_args = [(is_download, zip_file_url)]
    update_commit_sql = "UPDATE github_archive_dataset SET is_download = %s WHERE archive_id = %s"

    if zip_file_is_downloaded == '1':
        return current_line + 1

    try:
        target_file_path = unzip_file_path + unzip_file_name
        download_gzfile_and_unzip(zip_file_url, target_file_path)
        filter_json_by_commit_message(target_file_path)
        update_row(update_commit_sql, update_commit_args)

        print('current_line is ', str(current_line))
        if current_line % 24 == 0:
            print('current_line is ', str(current_line), '     !!!!!!!!!rewrite filter_commits_dict')
            write_filter_commits_into_txt(filter_file_path + filter_commits_dict_file_name, filter_commits_dict.values())
            load_filter_commits_dict_from_txt(filter_file_path + filter_commits_dict_file_name)

        return current_line + 1
    except Exception:
        print('!!!!!!!!!!!!!!!there are exceptions!')
        traceback.print_exc()
        return current_line + 1

def execute_download_daily_event():
    query_sql = "SELECT * FROM github_archive_dataset ORDER BY archive_id DESC"
    total_zip_info_list = db_query(query_sql)
    zip_file_list_count = len(total_zip_info_list)
    load_filter_commits_dict_from_txt(filter_file_path + filter_commits_dict_file_name)
    print('initial filtered commits count is: ', len(filter_commits_dict.values()))
    current_line = 0
    while current_line < zip_file_list_count:
        error_at = load_information_from_database_and_download_daily_event(current_line, total_zip_info_list)
        current_line = error_at

# execute_download_daily_event()





def clear_table(update_sql):
    db = pymysql.connect(host="127.0.0.1", user="username", password="password", db="crawled_data", port=3306)
    cursor = db.cursor()
    try:
        cursor.execute(update_sql)
        db.commit()
        effectedRows = cursor.rowcount
        print('update_row---effectedRows---', effectedRows)
    except:
        traceback.print_exc()
        db.rollcack()

    db.close()

def update_for_daily_event():
    query_sql = "SELECT * FROM github_archive_dataset"
    total_zip_info_list = db_query(query_sql)
    changed_list = []
    for zip_info in total_zip_info_list:
        print(zip_info)
        url_str = zip_info[0]
        time_str = zip_info[1]
        if time_str < '2021-10-1-0.json':
            is_crawled = '0'
        else:
            is_crawled = '1'
        one_list_item = []
        one_list_item.append(str(url_str))
        one_list_item.append(str(time_str))
        one_list_item.append(str(is_crawled))
        changed_list.append(one_list_item)
    delete_sql = "delete from github_archive_dataset"
    clear_table(delete_sql)
    insert_data_sql = "INSERT INTO github_archive_dataset(archive_id, unzip_file_name, is_download) VALUES (%s, %s, %s)"
    insert_rows(insert_data_sql, changed_list)


# update_for_daily_event()



# download
def download_daily_event():
    year_list = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    month_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    starttime = datetime.datetime.now()
    for year in year_list:
        for month in month_list:
            total_days = get_total_day_of_month(year, month)
            days_list = get_total_days_list(total_days)
            for day in days_list:
                for hour in range(24):
                    file_name_prefix = year + '-' + month + '-' + day + '-' + str(hour)

                    zip_file_name = str(file_name_prefix) + '.json.gz'
                    zip_file_url = baseURL + zip_file_name

                    unzip_file_name = str(file_name_prefix) + '.json'
                    target_file_path = unzip_file_path + unzip_file_name

                    download_gzfile_and_unzip(zip_file_url, target_file_path)

                    filter_json_by_commit_message(target_file_path, unzip_file_name)

    write_filter_commits_into_txt(filter_file_path + 'final_total_filter_commits.json', filter_commits_dict.values())
    endtime = datetime.datetime.now()
    print(endtime - starttime)

# download_daily_event()

def download_daily_event_zip_directly():
    year_list = ['2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012']
    month_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    password = 'password'

    starttime = datetime.datetime.now()
    for year in year_list:
        for month in month_list:
            total_days = get_total_day_of_month(year, month)
            days_list = get_total_days_list(total_days)
            for day in days_list:
                for hour in range(24):
                    file_name_prefix = year + '-' + month + '-' + day + '-' + str(hour)

                    zip_file_name = str(file_name_prefix) + '.json.gz'
                    zip_file_url = baseURL + zip_file_name
                    print('start to download ', zip_file_url)
                    # os.system('wget ' + zip_file_url)
                    command = 'wget ' + zip_file_url
                    os.system('echo %s | sudo -S %s' % (password, command))
                    print('finish download ', zip_file_url)

    endtime = datetime.datetime.now()
    print(endtime - starttime)

# download_daily_event_zip_directly()

def insert_daily_event_into_database():
    year_list = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    month_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    total_data_list = []
    starttime = datetime.datetime.now()
    for year in year_list:
        for month in month_list:
            total_days = get_total_day_of_month(year, month)
            days_list = get_total_days_list(total_days)
            for day in days_list:
                for hour in range(24):
                    file_name_prefix = year + '-' + month + '-' + day + '-' + str(hour)

                    zip_file_name = str(file_name_prefix) + '.json.gz'
                    zip_file_url = baseURL + zip_file_name
                    unzip_file_name = str(file_name_prefix) + '.json'

                    one_data_list = []
                    one_data_list.append(zip_file_url)
                    one_data_list.append(unzip_file_name)
                    one_data_list.append('0')

                    total_data_list.append(one_data_list)

    insert_data_sql = "INSERT INTO github_archive_dataset(archive_id, unzip_file_name, is_download) VALUES (%s, %s, %s)"
    insert_rows(insert_data_sql, total_data_list)
    endtime = datetime.datetime.now()
    print(endtime - starttime)

# insert_daily_event_into_database()


def combine_all_simplification_related_commit_json_files(json_file_path):
    print('combine_all_simplification_related_commit_json_files...')
    total_commit_list = []
    for root, dirs, files in os.walk(json_file_path):
        for file_name in files:
            total_commit_list.extend(read_json_file_by_lines(str(json_file_path) + str(file_name)))

    print('--len of total_commit_list--', len(total_commit_list))

    write_filter_commits_into_txt('./totalcommits/total_filter_commits.json', total_commit_list)

# combine_all_simplification_related_commit_json_files('./filterfiles/')


def add_is_crawled_pairs(commit_json_file_path):
    filter_commit_list = read_json_file_by_lines(commit_json_file_path)
    new_commit_list = []
    for filter_commit in filter_commit_list:
        filter_commit["is_crawled"] = "0"
        filter_commit["is_real"] = "0"
        new_commit_list.append(filter_commit)

    write_filter_commits_into_txt(commit_json_file_path, new_commit_list)

# add_is_crawled_pairs('filterfiles/total_filter_commits.json')

def save_simplified_information_into_database(commit_json_file_path):
    filter_commit_list = read_json_file_by_lines(commit_json_file_path)
    total_commit_information_list = []
    for filter_commit in filter_commit_list:
        one_commit_information = []
        one_commit_information.append(str(filter_commit["sha"]))
        one_commit_information.append(str(filter_commit["author"]["name"]))
        one_commit_information.append(str(filter_commit["author"]["email"]))
        one_commit_information.append(str(filter_commit["message"]))
        one_commit_information.append(str(filter_commit["distinct"]))
        one_commit_information.append(str(filter_commit["url"]))
        one_commit_information.append(str(filter_commit["is_crawled"]))
        one_commit_information.append(str(filter_commit["is_real"]))

        total_commit_information_list.append(one_commit_information)

    insert_sql = "INSERT INTO github_simplified_commit(sha, author_name, author_email, message, is_distinct, url, is_crawled, is_real) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    insert_rows(insert_sql, total_commit_information_list)

# save_simplified_information_into_database('filterfiles/total_filter_commits.json')


def filter_real_commits_by_conditions(extractor, current_line, filter_commit_list):
    simplification_related_commit = filter_commit_list[current_line]

    commit_is_crawled = simplification_related_commit[-2]
    if commit_is_crawled == "1":
        return current_line + 1

    # if this commit is crawled, move to the next commit
    commit_sha = simplification_related_commit[0]
    commit_api_url = simplification_related_commit[-3]
    commit_message = simplification_related_commit[3]

    split_url_str = commit_api_url.split('/')
    repo_name = split_url_str[4] + '/' + split_url_str[5]

    print('--start processing current line -------', current_line, '---total line is---', len(filter_commit_list))
    print('--current commit_api_url is--', commit_api_url)

    is_crawled = '1'
    is_real = '1'
    is_not_real = '0'

    invalid_update_args = [(is_crawled, is_not_real, commit_sha)]
    invalid_update_sql = "UPDATE github_simplified_commit SET is_crawled = %s and is_real = %s WHERE sha = %s"

    try:
        # get the repository and commit objects by PyGitHub's APIs
        repo = g.get_repo(repo_name)
        commit = repo.get_commit(sha=commit_sha)

        changed_file_list = commit.files

        if len(changed_file_list) == 0:
            update_row(invalid_update_sql, invalid_update_args)
            return current_line + 1

        commit_parents_list = commit.parents

        # if commit has more than one parent, then pass this commit
        if len(commit_parents_list) != 1:
            update_row(invalid_update_sql, invalid_update_args)
            return current_line + 1

        # check if changed files contain java file
        is_contain_java_file = False
        for changed_file in changed_file_list:
            changed_file_name = changed_file.filename
            if changed_file_name.endswith('.java'):
                is_contain_java_file = True
                break

        if is_contain_java_file == False:
            update_row(invalid_update_sql, invalid_update_args)
            return current_line + 1

        # the parent commit sha
        commit_parent_sha = commit_parents_list[0].sha



        total_changed_method_list = []

        # resolve each changed java file
        for changed_file in changed_file_list:
            changed_file_name = changed_file.filename

            # focus only on java file
            if changed_file_name.endswith('.java'):
                additions_line = changed_file.additions
                deletions_line = changed_file.deletions

                # # only delete or add lines, ignore
                # if additions_line == 0 or deletions_line == 0:
                #     continue
                #
                # # add more lines than deleted lines, ignore
                # if additions_line > deletions_line:
                #     continue

                # current commit and parent commit, two version files
                change_file_url = 'https://raw.githubusercontent.com/' + repo_name + '/' + commit_sha + '/' + changed_file_name
                original_file_url = 'https://raw.githubusercontent.com/' + repo_name + '/' + commit_parent_sha + '/' + changed_file_name

                print("change_file_url is : ", change_file_url)
                print("original_file_url is : ", original_file_url)
                # the content of the url
                changed_file_content = requests.get(change_file_url).text
                original_file_content = requests.get(original_file_url).text

                print('--------404-----------', ("404: Not Found" == str(original_file_content)) or ("404: Not Found" == str(changed_file_content)))
                # if any of those file can not be found, ignore current file
                if ("404: Not Found" == str(original_file_content)) or ("404: Not Found" == str(changed_file_content)):
                    continue

                # the fold and the file to be created, then we can use javaparser to parse those java file
                fold_to_generate_file = 'generatejava/'
                original_java_file_name = "original.java"
                changed_java_file_name = "changed.java"

                # create java file according to the original_file content, if create fail, pass this file
                original_file_create_res = create_java_file(fold_to_generate_file, original_java_file_name, original_file_content)
                if original_file_create_res == False:
                    continue

                # create the changed java file according to the changed_file content
                changed_filecreate_res = create_java_file(fold_to_generate_file, changed_java_file_name, changed_file_content)
                if changed_filecreate_res == False:
                    delete_java_file(fold_to_generate_file, original_java_file_name)
                    continue

                # file patch
                changed_file_patch = changed_file.patch

                # get all diff hunk head
                lines_list = re.findall(r"@@\s([-\+]?\d+,[-\+]?\d+)\s([-\+]?\d+,[-\+]?\d+)", changed_file_patch)

                # get start line and continuous lines of original file and changed file
                for lines in lines_list:
                    original_file_lines = str(lines[0])[1:].split(',')
                    original_file_lines_context_start_line = int(original_file_lines[0])
                    original_file_lines_continuous_lines = original_file_lines[1]
                    original_file_lines_change_start_line = original_file_lines_context_start_line + 3


                    changed_file_lines = str(lines[1])[1:].split(',')
                    changed_file_lines_context_start_line = int(changed_file_lines[0])
                    change_file_lines_continuous_lines = changed_file_lines[1]
                    changed_file_lines_change_start_line = changed_file_lines_context_start_line + 3

                    # extract method information from original class according to the original_file_lines_change_start_line
                    original_method_information = extractor.getTargetMethod(fold_to_generate_file + original_java_file_name, str(original_file_lines_change_start_line))
                    if original_method_information is None or len(str(original_method_information)) == 0 or original_method_information == "None":
                        continue

                    # extract method information from original class according to the change_file_lines_change_start_line
                    changed_method_information = extractor.getTargetMethod(fold_to_generate_file + changed_java_file_name, str(changed_file_lines_change_start_line))
                    if changed_method_information is None or len(str(changed_method_information)) == 0 or changed_method_information == "None":
                        continue

                    # convert the java String to Python str
                    original_method_information = str(original_method_information)
                    changed_method_information = str(changed_method_information)

                    print('------extracted method information from original class------')
                    print(original_method_information)
                    print('------extracted method information from original class------')
                    print('------extracted method information from changed class------')
                    print(changed_method_information)
                    print('------extracted method information from changed class------')

                    # convert str to json, so we can get the item in the json object easily
                    original_method_information_json = json.loads(original_method_information)
                    changed_method_information_json = json.loads(changed_method_information)

                    original_method_name_str = original_method_information_json["name"]
                    changed_method_name_str = changed_method_information_json["name"]

                    # if the changed method is main method, ignore
                    if original_method_name_str == "main" or changed_method_name_str == "main":
                        continue

                    # if not the same method name, continue
                    if original_method_name_str != changed_method_name_str:
                        continue

                    original_method_end_line = str(original_method_information_json["end_line"])
                    changed_method_end_line = str(changed_method_information_json["end_line"])

                    # if the changed content is not contained in a method, ignore
                    if original_file_lines_change_start_line + (original_file_lines_continuous_lines - 6) - 1 > original_method_end_line or \
                            changed_file_lines_change_start_line + (change_file_lines_continuous_lines - 6) - 1 > changed_method_end_line:
                        print('changed content is out of the method range, ignore')
                        continue

                    original_method_without_comment = str(original_method_information_json["declaration"]) + str(original_method_information_json["method_body_without_comment"])
                    changed_method_without_comment = str(changed_method_information_json["declaration"]) + str(changed_method_information_json["method_body_without_comment"])

                    '''
                    the following operations is to filter the method data.
                    1. if the original method is equal to base method, it means the method not changed, ignore this kind of method
                    2. if the original method or changed method contains more than 512 tokens, then ignore those, because the deep learning 
                       model can not process such a long token sequence.
                    '''

                    if original_method_without_comment == changed_method_without_comment:
                        print('the method is not changed from original java file to changed java file, ignore this')
                        continue

                    if len(word_tokenize(changed_method_without_comment)) > 512 or len(word_tokenize(original_method_without_comment)) > 512:
                        print('the method tokens are more than 512, ignore this')
                        continue

                    one_changed_method_information_list = []
                    one_changed_method_information_list.append(commit_sha)
                    one_changed_method_information_list.append(commit_api_url)
                    one_changed_method_information_list.append(commit_message)
                    one_changed_method_information_list.append(changed_file_name)
                    one_changed_method_information_list.append(str(original_file_lines_change_start_line))
                    one_changed_method_information_list.append(str(changed_file_lines_change_start_line))
                    one_changed_method_information_list.append(original_method_without_comment)
                    one_changed_method_information_list.append(changed_method_without_comment)
                    total_changed_method_list.append(one_changed_method_information_list)

        # insert changed method information into database
        insert_changed_method_sql = "INSERT INTO github_changed_method(commit_sha, commit_api_url, commit_message, file_name, original_file_lines_change_start_line, changed_file_lines_change_start_line, " \
                                    "original_method_without_comment, changed_method_without_comment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        insert_rows(insert_changed_method_sql, total_changed_method_list)

        print('!!!!!!successful get a commit changed methods')

        # update commit information into database
        update_commit_args = [(is_crawled, is_real, commit_sha)]
        update_commit_sql = "UPDATE github_simplified_commit SET is_crawled = %s and is_real = %s WHERE sha = %s"
        update_row(update_commit_sql, update_commit_args)

        return current_line + 1
    # this is for the github.GithubException.RateLimitExceededException: 403
    except RateLimitExceededException:
        traceback.print_exc()
        search_rate_limit = g.get_rate_limit().search
        print('search remaining', format(search_rate_limit.remaining))
        reset_timestamp = calendar.timegm(search_rate_limit.reset.timetuple())
        # add 10 seconds to be sure the rate limit has been reset
        sleep_time = reset_timestamp - calendar.timegm(time.gmtime()) + 10
        time.sleep(sleep_time)
        return current_line
    except Exception:
        print('!!!!!!!!!!!!!!!there are exceptions!')
        traceback.print_exc()
        update_row(invalid_update_sql, invalid_update_args)
        return current_line + 1



def execute_filter_real_commits_by_conditions():
    query_sql = "SELECT * FROM github_simplified_commit"
    filter_commit_list = db_query(query_sql)
    filter_commit_list_count = len(filter_commit_list)
    current_line = 0

    start_jvm()

    # load the function and class information extractor from jar
    Extractor = jpype.JClass("com.example.first.FunctionAndClassInformationExtractor")
    extractor = Extractor()

    while current_line < filter_commit_list_count:
        error_at = filter_real_commits_by_conditions(extractor, current_line, filter_commit_list)
        current_line = error_at

    shut_jvm()

execute_filter_real_commits_by_conditions()