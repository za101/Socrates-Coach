from werkzeug.security import generate_password_hash, check_password_hash

password = 'rhp'
password_hash = generate_password_hash(password)
print(password_hash)