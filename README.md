# Automated-Program-Simplification

### Tables in Current Repo
the table ``resource/table/Simplifacation_study.md`` is studied pr link with simplification type in the whole study.

the table ``resource/table/motivation_with_type.md`` is the studied pr link with simplification type in the motivation study, while
the table ``resource/table/motivation_with_commitMessage.md`` is the studied pr link with commit message in the motivation study.





### Experimental Setup
**The CodeXGLUE and dataset are at** <https://zenodo.org/records/12176049>.

After downloading the code and dataset files, unzip it. The dataset is in the ``dataset.zip`` on zenodo,
the code is in the ``resource/code_to_prompts_codet5/prompts_codet5`` folder, the running environment is in ``resource/code_to_prompts_codet5/environment.txt``.

And the CodeXGLUE we used is in ``CodeXGLUE.zip``,please extract it to folder ``resource/code_to_prompts_codet5/prompts_codet5`` bdefore use.

we run this code on ``Ubuntu16.04`` and ``python 3.8.17``, you need to install the dependency according to ``resource/code_to_prompts_codet5/environment.txt``, 
choose the right version of pytorch according to you cuda version.

### Datasets
in ``dataset/remove_duplication``, the folders and files are following:
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
in ``resource/code_to_prompts_codet5/prompts_codet5``
you can choose to run on different setting by copying different dataset into ``resource/code_to_prompts_codet5/prompts_codet5/data`` folder.
For example, if you want to training and testing on tagged dataset, you need to copy the json file in ``dataset/remove_duplication/tagged/``
into ``resource/code_to_prompts_codet5/prompts_codet5/data``. You can choose to test on big test dataset (``dataset/remove_duplication/tagged/test.jsonl``) or 
small validate dataset (``dataset/remove_duplication/tagged/small/test.jsonl``).

We have uploaded our crawler together with the dependency into the repository. This crawler is to crawl program simplification data to tune the CodeT5, the crawler is at (``resource/crawler.py``).

### Predictions and Evalution
copy the dataset into the ``resource/code_to_prompts_codet5/prompts_codet5/data`` file, run ``./start_prompts.sh`` in folder``resource/code_to_prompts_codet5/prompts_codet5``.

after finishing the tuning and testing. To **evalute** the generated simplification: run ``./start_cal_code_bleu.sh`` also in folder``resource/code_to_prompts_codet5/prompts_codet5``.



### SomethingElse
If you want to **change the parameters of tuning**, you can edit the ``resource/code_to_prompts_codet5/prompts_codet5/start_prompts.sh``. 
If you want to **change more paramters**, you can refer to the ``resource/code_to_prompts_codet5/prompts_codet5/finetune_t5_gene.py`` for editing.


If you need to **compare the cognitive complexity and cyclomatic complexity** of the code, you can refer to <https://docs.pmd-code.org/pmd-doc-6.55.0/pmd_rules_java_design.html#cognitivecomplexity> for the configuration of relevant PMD rules.Our ruleset is like this:
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

### Following are the issues that we submitted to RefactoringMiner

<https://github.com/tsantalis/RefactoringMiner/issues/678>

<https://github.com/tsantalis/RefactoringMiner/issues/679>

<https://github.com/tsantalis/RefactoringMiner/issues/681>

<https://github.com/tsantalis/RefactoringMiner/issues/682>

<https://github.com/tsantalis/RefactoringMiner/issues/680>

<https://github.com/tsantalis/RefactoringMiner/issues/683>

<https://github.com/tsantalis/RefactoringMiner/issues/684>

<https://github.com/tsantalis/RefactoringMiner/issues/685>

