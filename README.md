# Automated-Program-Simplification

The code and dataset are at .



After you download the code and dataset files, unzip it. The dataset is in the ../dataset folder,
the code is in the prompts_codet5.zip, the running environment is in environment.txt

To run the code, you need to do the following:
1. we run this code on Ubuntu16.04 and python 3.8.17, you need to install the dependency according to environment.txt, 
choose the right version of pytorch according to you cuda version.
2. unzip prompts_codet5.zip
3. unzip dataset.zip, the floders and files are following:
-initial_dataset
--small
---equivalent_items.txt (small validate dataset meta information)
--test_dataset.txt (whole test dataset meta information)
--train_dataset.txt (whole train dataset meta information)
--valid_dataset.txt (whole valid dataset meta information)
-tagged (tagged dataset)
--json
---small
----test.jsonl (tagged small validate json format dataset)
---test.jsonl (tagged whole test json format dataset)
---train.jsonl (tagged whole train json format dataset)
---valid.jsonl (tagged whole valid json format dataset)
-untagged (untagged dataset)
--json
---small
----test.jsonl (untagged small validate json format dataset)
---test.jsonl (untagged whole test json format dataset)
---train.jsonl (untagged whole train json format dataset)
---valid.jsonl (untagged whole valid json format dataset)

2. cd prompts_codet5
you can choose to run on different setting by copying different dataset into ./data folder.
For example, if you want to training and testing on tagged dataset, you need to copy the json file in ../dataset/tagged/
into ./data. You can choose to test on big test dataset (../dataset/tagged/test.jsonl) or 
small validate dataset (../dataset/tagged/small/test.jsonl).

3. after you copy the dataset into the ./data file, run ./start_prompts.sh

4. after finishing the tuning and testing. To evalute the generated simplification: run ./start_cal_code_bleu.sh

If you want to change the parameters of tuning, you can edit the start_prompts.sh. 
If you want to change more paramters, you can refer to the finetune_t5_gene.py for editing.