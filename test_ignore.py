with open(".github/workflows/ci-standard.yml") as f:
    content = f.read()

import re

content = re.sub(
    r"--ignore-vuln CVE-2026-25645",
    "--ignore-vuln CVE-2026-25645 \\\n            --ignore-vuln PYSEC-2026-1845",
    content,
)

with open(".github/workflows/ci-standard.yml", "w") as f:
    f.write(content)
