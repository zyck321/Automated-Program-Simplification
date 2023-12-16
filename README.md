# Automated-Program-Simplification

### tables in repo
the table ``Simplifacation_study`` is studied pr link with simplification type in the whole study.

the table ``motivation_with_type`` is the studied pr link with simplification type in the motivation study, while
the table ``motivation_with_commitMessage`` is the studied pr link with commit message in the motivation study.



**The code and dataset are at** https://zenodo.org/records/10390542.

After downloading the code and dataset files, unzip it. The dataset is in the ``../dataset`` folder,
the code is in the ``prompts_codet5.zip``, the running environment is in ``environment.txt``.

### Experimental Setup
we run this code on ``Ubuntu16.04`` and ``python 3.8.17``, you need to install the dependency according to ``environment.txt``, 
choose the right version of pytorch according to you cuda version.

### Datasets
unzip ``dataset.zip``, the folders and files are following:
```
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
```
in ``prompts_codet5``
you can choose to run on different setting by copying different dataset into ``./data`` folder.
For example, if you want to training and testing on tagged dataset, you need to copy the json file in ``../dataset/tagged/``
into ``./data``. You can choose to test on big test dataset (``../dataset/tagged/test.jsonl``) or 
small validate dataset (``../dataset/tagged/small/test.jsonl``).

### Predictions and Evalution
copy the dataset into the ``./data`` file, run ``./start_prompts.sh``

after finishing the tuning and testing. To **evalute** the generated simplification: run ``./start_cal_code_bleu.sh``.



### SomethingElse
If you want to **change the parameters of tuning**, you can edit the ``start_prompts.sh``. 
If you want to **change more paramters**, you can refer to the ``finetune_t5_gene.py`` for editing.

If you want to **find duplicated code with CPD**, please view ``https://docs.pmd-code.org/pmd-doc-6.31.0/pmd_userdocs_cpd.html`` for detail information.

If you need to **compare the cognitive complexity and cyclomatic complexity** of the code, you can refer to ``https://docs.pmd-code.org/pmd-doc-6.55.0/pmd_rules_java_design.html#cognitivecomplexity`` for the configuration of relevant PMD rules.Our ruleset is like this:
```
<rule ref="category/java/design.xml/CognitiveComplexity">
    <properties>
        <property name="reportLevel" value="1" />
    </properties>
</rule>
<rule ref="category/java/design.xml/CyclomaticComplexity">
    <properties>
        <property name="classReportLevel" value="80" />
        <property name="methodReportLevel" value="1" />
        <property name="cycloOptions" value="" />
    </properties>
</rule>
```
