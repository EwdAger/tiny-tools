import pandas as pd
import yaml

data = pd.read_csv(r"hosts.csv")

ip = data.loc[:, "ip"].tolist()
hosts = data.loc[:, "hosts"].tolist()

res = {
    "hostAliases": []
}

for i in range(len(ip)):
    res_side = {
        "ip": f"\"{ip[i]}\"",
        "hostnames": [f"\"{hosts[i]}\""]
    }
    res['hostAliases'].append(res_side)

with open('hosts.yaml', 'w') as f:
    yaml.dump(res, f)
    f.close()
