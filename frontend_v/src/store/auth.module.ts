import AuthService from '@/services/auth/auth.service';
import {tokenService} from "@/services/auth/token.service";
import {LoginUser, User, UserTokens} from "@/services/user";
import UserService, {getMyselfData} from "@/services/auth/user.service";

class Status {
    constructor(
        public loggedIn: boolean,
    ) {}
}

class UserState {
    constructor(
        public status: Status,
        public user: User | null,
        public userTokens: UserTokens,
    ) {}
}

const user = UserService.getUser()
const initialState = new UserState(
    new Status(user !== null && user.username?.length > 0),
    user,
    tokenService.getUserTokens(),
)


export const auth = {
    namespaced: true,
    state: initialState,
    actions: {
        login({ commit }: any, user: LoginUser) {
            return AuthService.login(user).then(
                (data) => {
                    if (data.status == 200) commit('loginSuccess');
                    return Promise.resolve(data);
                },
                error => {
                    commit('loginFailure');
                    return Promise.reject(error);
                }
            );
        },
        async keycloakLogin({commit}: any) {
            await AuthService.keycloakLogin();
            commit('loginSuccess')
            return Promise.resolve()
        },
        async logout({ commit }: any) {
            await AuthService.logout();
            commit('logout');
        },
        refreshTokens({ commit }: any, tokens: any) {
            commit('refreshTokens', tokens);
        }
    },
    mutations: {
        loginSuccess(state: UserState) {
            state.status.loggedIn = true;
            getMyselfData().then(
                user => {
                    UserService.setUser(user)
                    state.user = user
                    state.userTokens = tokenService.getUserTokens()
                }
            )
        },
        loginFailure(state: UserState) {
            state.status.loggedIn = false;
            state.user = null;
        },
        logout(state: UserState) {
            state.status.loggedIn = false;
            state.user = null;
        },
        refreshTokens(state: UserState, {access, refresh}: any) {
            state.status.loggedIn = true;
            state.userTokens.accessToken = access;
            state.userTokens.refreshToken = refresh;
        }
    }
};