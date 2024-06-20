import statistics
import subprocess
from tqdm import tqdm
import javalang
import pandas as pd


def tokenize_java(code):
    token_gen = javalang.tokenizer.tokenize(code)
    tokens = []
    indexes = []
    while (True):
        try:
            token = next(token_gen)
        except:
            break
        tokens.append(token)

    pure_tokens = [token.value for token in tokens]

    return pure_tokens


def code_bleu(ref, hyp):
    f = open('./ref.txt', 'w', encoding='utf-8')
    f.write(ref)
    f.close()
    f = open('./hyp.txt', 'w', encoding='utf-8')
    f.write(hyp)
    f.close()

    f = open('codeBleu.sh', 'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('cd ./CodeXGLUE/Code-Code/code-to-code-trans/evaluator/CodeBLEU && ' +
            'python3 calc_code_bleu.py --refs ' + path_ref +
            ' --hyp ' + path_hyp + ' --lang java --params 0.25,0.25,0.25,0.25' +
            ' > bleu.log')
    f.close()

    subprocess.run('./codeBleu.sh', shell=True)
    result = [line.strip() for line in open(path_result)]
    if len(result) == 3:
        f = open('codeBleu.sh', 'w')
        f.write('#!/usr/bin/env bash\n')
        f.write('cd ./CodeXGLUE/Code-Code/code-to-code-trans/evaluator/CodeBLEU && ' +
                'python3 calc_code_bleu.py --refs ' + path_ref +
                ' --hyp ' + path_hyp + ' --lang java --params 0.25,0.25,0.25,0' +
                ' > bleu.log')
        f.close()
        subprocess.run('./codeBleu.sh', shell=True)
        result = [line.strip() for line in open(path_result)]
        return float(result[-1].split()[2])
    try:
        return float(result[-1].split()[2])
    except:
        print('.............................................WARNING.............................................')
        return 0


for BEAM_SIZE in [10]:

    print('BEAM SIZE: ', BEAM_SIZE)

    # change the following path with your correct paths to:
    # - path_targets : targets file
    # - path_predictions : predictions file
    # - path_statistics : the file where the statistics will be saved


    path_targets = './pr_model/test.gold'
    path_predictions = './pr_model/test.output'
    path_statistics = './pr_model/statistics.txt'

    # df = pd.read_csv(path_targets, sep='\t', names=['source', 'target'])
    # df = pd.read_csv(path_targets,  sep='\t', names=['target'])
    tgt = [line.strip() for line in open(path_targets, encoding='utf-8')]
    pred = [line.strip() for line in open(path_predictions, encoding='utf-8')]

    path_ref = '../../../../../ref.txt'
    path_hyp = '../../../../../hyp.txt'

    path_result = './CodeXGLUE/Code-Code/code-to-code-trans/evaluator/CodeBLEU/bleu.log'

    count_perfect = 0
    BLEUscore = []
    perfect_prediction_list = []
    for i in tqdm(range(len(tgt))):
        best_BLEU = 0
        target = tgt[i]
        for prediction in pred[i*BEAM_SIZE:i*BEAM_SIZE+BEAM_SIZE]:
            # when BEAM_SIZE > 1 select the best prediction


            try:
                current_pred = " ".join(tokenize_java(prediction))
                current_tgt = " ".join(tokenize_java(target))
            except:

                current_pred = prediction
                current_tgt = target

            if " ".join(current_pred.split()) == " ".join(current_tgt.split()):
                count_perfect += 1
                perfect_prediction_list.append(str(i))

                try:

                    best_BLEU = code_bleu(current_tgt, current_pred)
                except:
                    current_pred = prediction

                    current_tgt = target
                    best_BLEU = code_bleu(current_tgt, current_pred)

                break
            try:
                current_BLEU = code_bleu(current_tgt, current_pred)
            except:
                current_pred = prediction

                current_tgt = target
                current_BLEU = code_bleu(current_tgt, current_pred)

            if current_BLEU > best_BLEU:
                best_BLEU = current_BLEU
        BLEUscore.append(best_BLEU)

    print(f'PP    : %d/%d (%s%.2f)' % (count_perfect, len(tgt), '%', (count_perfect * 100) / len(tgt)))
    print(f'BLEU mean              : ', statistics.mean(BLEUscore))
    print(f'BLEU median            : ', statistics.median(BLEUscore))
    print(f'BLEU stdev             : ', statistics.stdev(BLEUscore))
    print('perfect prediction id list is: ')
    print(perfect_prediction_list)
    f = open(path_statistics, 'w+')
    f.write(f'PP     : %d/%d (%s%.2f)' % (count_perfect, len(tgt), '%', (count_perfect * 100) / len(tgt)))
    f.write('\nBLEU mean              : ' + str(statistics.mean(BLEUscore)))
    f.write('\nBLEU median            : ' + str(statistics.median(BLEUscore)))
    f.write('\nBLEU stdev             : ' + str(statistics.stdev(BLEUscore)))

    f.close()
