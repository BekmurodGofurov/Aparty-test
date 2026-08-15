import os

mapping = {
    'from app.domains.users.models import': 'from app.domains.users.models import',
    'from app.domains.users.models import': 'from app.domains.users.models import',
    'from app.domains.users.models import': 'from app.domains.users.models import',
    'from app.domains.apartments.models import': 'from app.domains.apartments.models import',
    'from app.domains.apartments.models import': 'from app.domains.apartments.models import',
    'from app.domains.orders.models import': 'from app.domains.orders.models import',
    'from app.domains.orders.models import': 'from app.domains.orders.models import',
    'from app.domains.orders.models import': 'from app.domains.orders.models import',
    'from app.domains.orders.models import': 'from app.domains.orders.models import',
    'from app.domains.orders.models import': 'from app.domains.orders.models import',
}

for root, _, files in os.walk('.'):
    if '.venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if not file.endswith('.py'):
            continue
        filepath = os.path.join(root, file)
        with open(filepath, 'r') as f:
            content = f.read()
        
        new_content = content
        for old, new in mapping.items():
            new_content = new_content.replace(old, new)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
