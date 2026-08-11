with open("SPEC.md", "r") as f:
    spec = f.read()

# Find the end of the changelog and append our entry
new_entry = "| 2026-07-29 | 1.0.38 | Optimized XML text escaping by conditionally invoking individual string replacements instead of chained unconditional replace calls. |\n"
spec = spec + new_entry

with open("SPEC.md", "w") as f:
    f.write(spec)
