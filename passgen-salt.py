import bcrypt, random, string, sys

def generate_username(prefix="Socrt", length=12):
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=length - len(prefix)))
    return prefix + suffix

def generate_password(length=16):
    # Exclude comma from punctuation
    #punctuation_without_comma = ''.join(char for char in string.punctuation if char != ',')
    punctuation_without_comma = ''.join(char for char in string.punctuation if char not in ('\'','"',',','*',';','`','/','.',';'))

    characters = string.ascii_letters + string.digits + punctuation_without_comma
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def salt_hash_password(password):
    # Generate a random salt
    salt = bcrypt.gensalt()
    #print("===salt:", salt)

    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Return the hashed password as a byte string
    return hashed_password

def check_password(input_password, stored_hashed_password):
    # Check if the input password matches the stored hashed password
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hashed_password)

salt_hashed_password = salt_hash_password("etphonehome")
print("====salt_hashed_password:", salt_hashed_password)
sys.exit()

# Example usage
num_user = 100
usernames = [generate_username() for _ in range(num_user)]
passwords = [generate_password() for _ in range(num_user)]

filename = "Socrates_User_Accounts.csv"
with open(filename, 'w') as file:

    file.write("seq, user_name, password, salt_hash" + '\n')

    for i, password in enumerate(passwords, start=1):
        hashed_password = salt_hash_password(password)
        file.write(f"{i}, {usernames[i-1]}, {password}, {hashed_password}" + '\n')
        #print("User Name:", i, usernames[i-1])
        #print("Original Password:", i, password)
        #print("Hashed Password:", i, hashed_password.decode('utf-8'))

        #Example usage
        input_password = password
        if check_password(input_password, hashed_password):
            print("Password is correct!", i, input_password)
        else:
            print("Password is incorrect.")

