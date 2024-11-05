class LoginUserIsValid {
    username: boolean = true
    usernameError: string = ""
    password: boolean = true
    passwordError: string = ""

    validateUsername(value: string): void {
        if (value.length <= 3) {
            this.username = false;
            this.usernameError = "Укажите более 3 символов";
            return;
        }
        this.username = true;
        this.usernameError = "";
    }

    validatePassword(value: string): void {
        if (value.length < 8) {
            this.password = false;
            this.passwordError = "Пароль должен быть 8 или более символов";
            return;
        }
        if (!value.match(/\d/) || !value.match(/\D/)) {
            this.password = false;
            this.passwordError = "Пароль должен состоять, как минимум, из цифр и букв";
            return;
        }
        this.password = true;
        this.passwordError = "";
    }

    get isValid(): boolean {
        return this.username && this.password;
    }

}

class LoginUser {
    username: string = ""
    password: string = ""
    readonly valid: LoginUserIsValid

    constructor() {
        this.valid = new LoginUserIsValid()
    }

    public get isValid(): boolean {
        this.valid.validateUsername(this.username)
        this.valid.validatePassword(this.password)
        return this.valid.isValid
    }

}

class User {
    constructor(
        public id: string,
        public username: string,
        public isSuperuser: boolean,
        public isStaff: boolean,
        public firstName?: string,
        public lastName?: string,
        public email?: string,
        public dateJoin?: string,
    ) {}
}

export interface UserTokens {
    accessToken: string;
    refreshToken: string;
}

function createNewUser(data: any): User {
    return new User(data.id, data.username, data.is_superuser, data.is_staff,
        data.first_name, data.last_name, data.email, data.date_join)
}

export {User, LoginUser, createNewUser}
