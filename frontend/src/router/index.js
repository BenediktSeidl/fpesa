import Vue from 'vue'
import Router from 'vue-router'
import Index from '@/components/Index'
import Dev from '@/components/Dev'
import Saved from '@/components/Saved'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Index',
      component: Index
    }, {
      path: '/dev/',
      name: 'Dev',
      component: Dev
    }, {
      path: '/saved/',
      name: 'Saved',
      component: Saved
    }
  ]
})
