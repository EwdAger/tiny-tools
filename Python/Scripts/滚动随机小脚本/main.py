# -*- coding: utf-8 -*-
"""
create at 2021/5/21

@author: EwdAger
"""

import time
import os
import random

args = ["a", "b", "c", "d", "e"]
last = ""

for i in range(0, 100, 5):
    os.system('cls' if os.name == 'nt' else 'clear')
    last = args[random.randint(0, len(args) - 1)]
    print(last, end="\n\n")
    time.sleep(float(f'{0.01 * i}'))

print(f"恭喜 {last}")
