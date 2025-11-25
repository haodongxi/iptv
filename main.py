import imp
import os
import requests
from urllib.parse import urljoin
import re
import sys
import json
import arrange_channel as ac
import re_check as rc
import check as ck
import parse as pr

# 使用示例
if __name__ == "__main__":
    dict = sys.argv
    if dict is None or len(dict) <= 1:
        print("参数为空")
    else:
        type = dict[1]
        if type == "all":
            pr.main()
            ck.main()
            ac.main()
        elif type == "component":
            rc.main()
        else :
            print("暂时没有方式可以处理")
