import re
import os

skill_file = "skills/hexagonal-architecture/SKILL.md"
with open(skill_file, "r") as f:
    lines = f.readlines()

# Very simple state machine
frontmatter = []
core = []
layer_rules = []
testing = []
examples = []

state = "frontmatter"

def normalize_header(line):
    return line.strip().lower()

for line in lines:
    header = normalize_header(line)
    
    if state == "frontmatter":
        frontmatter.append(line)
        if line.strip() == "---" and len(frontmatter) > 1:
            state = "core"
        continue
        
    if header.startswith("## reglas por capa"):
        state = "layer_rules"
    elif header.startswith("## transacciones"):
        state = "testing"
    elif header.startswith("## flujo para implementar una funcionalidad"):
        state = "core_end"
    
    if state == "core":
        core.append(line)
    elif state == "layer_rules":
        layer_rules.append(line)
    elif state == "testing":
        testing.append(line)
    elif state == "core_end":
        core.append(line)

new_skill = "".join(frontmatter) + "".join(core)
new_skill = new_skill.replace("## Estructura de cada módulo", "## References\n\n- Detailed layer rules: [Layer Rules](references/01_layer_rules.md)\n- Testing & Transactions: [Testing](references/02_testing_and_transactions.md)\n\n## Estructura de cada módulo")

with open("skills/hexagonal-architecture/SKILL.md", "w") as f:
    f.write(new_skill)

with open("skills/hexagonal-architecture/references/01_layer_rules.md", "w") as f:
    f.write("# Reglas por capa\n\n" + "".join(layer_rules[1:]))

with open("skills/hexagonal-architecture/references/02_testing_and_transactions.md", "w") as f:
    f.write("# Pruebas y Transacciones\n\n" + "".join(testing[1:]))

print("Skill successfully split!")
