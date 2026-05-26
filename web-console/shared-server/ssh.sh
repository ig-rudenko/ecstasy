clear;
read -r -p "Enter username: " username;
ssh "$username"@"$1" -p 22;