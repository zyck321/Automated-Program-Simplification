#!/usr/bin/env bash
cd ./CodeXGLUE/Code-Code/code-to-code-trans/evaluator/CodeBLEU && python3 calc_code_bleu.py --refs ../../../../../ref.txt --hyp ../../../../../hyp.txt --lang java --params 0.25,0.25,0.25,0.25 > bleu.log