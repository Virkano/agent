import { hasPermission, set_next_route } from '@/utils/permission/index'
import { getChildRouteList } from '@/router/common'
import NProgress from 'nprogress'
import { getPermissionRoute } from '@/router/common'
import {
  createRouter,
  createWebHistory,
  type NavigationGuardNext,
  type RouteLocationNormalized,
  type RouteRecordName,
} from 'vue-router'
import useStore from '@/stores'
import { routes } from '@/router/routes'
NProgress.configure({ showSpinner: false, speed: 500, minimum: 0.3 })
const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_BASE_PATH || window.TelecomAI?.prefix || import.meta.env.BASE_URL),
  routes: routes,
})

const initChatRoute = async (
  to: RouteLocationNormalized,
  next: NavigationGuardNext,
) => {
  const { chatUser } = useStore()
  chatUser.setAccessToken(to.params.accessToken.toString())

  let authentication = false
  try {
    authentication = await chatUser.isAuthentication()
  } catch (e: any) {
    next()
    return
  }

  const p_token = to.query.token
  if (p_token) {
    chatUser.setToken(p_token as string)
  }
  const token = chatUser.getToken()

  if (authentication) {
    if (!token && to.name !== 'UserLogin') {
      next({
        name: 'UserLogin',
        params: {
          accessToken: to.params.accessToken,
        },
        query: to.query,
      })
      return
    }
    if (to.name === 'UserLogin') {
      next()
      return
    }
    try {
      await chatUser.applicationProfile()
      if (chatUser.chat_profile?.authentication_type === 'login') {
        await chatUser.getChatUserProfile()
      }
    } catch (e: any) {
      if (e.response?.status === 401) {
        next({
          name: 'UserLogin',
          params: {
            accessToken: to.params.accessToken,
          },
          query: to.query,
        })
      }
      return
    }
    if (p_token) {
      const q = { ...to.query }
      delete q.token
      next({ ...to, query: q })
    } else {
      next()
    }
    return
  }

  try {
    if (!token) {
      await chatUser.anonymousAuthentication()
    }
    await chatUser.applicationProfile()
  } catch (e: any) {
    next()
    return
  }
  next()
}

// 路由前置拦截器
router.beforeEach(
  async (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    NProgress.start()
    if (to.name === '404') {
      next()
      return
    }
    const { user, login } = useStore()

    const notAuthRouteNameList = ['login', 'ForgotPassword', 'ResetPassword', 'Chat', 'UserLogin']
    if (['Chat', 'UserLogin'].includes(to.name ? to.name.toString() : '')) {
      await initChatRoute(to, next)
      return
    }
    if (!notAuthRouteNameList.includes(to.name ? to.name.toString() : '')) {
      if (to.query && to.query.token) {
        localStorage.setItem('token', to.query.token.toString())
      }
      const token = login.getToken()
      if (!token) {
        next({
          path: '/login',
        })
        return
      }
      if (!user.userInfo) {
        await user.profile()
      }
    }
    set_next_route(to)
    // 判断是否有菜单权限
    if (to.meta.permission ? hasPermission(to.meta.permission as any, 'OR') : true) {
      if(to.name=='noPermissionD'){
         const n = getPermissionRoute(routes, to)
         if(n.name=='noPermission'){
          next()
          return
         }else{
          next(n)
          return
         }
      }else{
        next()
      }
    } else {
      const n = getPermissionRoute(routes, to)
      next(n)
    }
  },
)
router.afterEach(() => {
  NProgress.done()
})
export const getChildRouteListByPathAndName = (path: any, name?: RouteRecordName | any) => {
  return getChildRouteList(routes, path, name)
}

export default router
