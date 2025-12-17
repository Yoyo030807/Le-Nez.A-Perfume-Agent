import DefaultTheme from 'vitepress/theme'
import './styles.css'
import PerfumeChat from './components/PerfumeChat.vue'
import Atelier from './components/Atelier.vue'
import LandingPage from './components/LandingPage.vue'
import Lab from './components/Lab.vue'

export default {
  ...DefaultTheme,
  enhanceApp({ app }) {
    app.component('PerfumeChat', PerfumeChat)
    app.component('Atelier', Atelier)
    app.component('LandingPage', LandingPage)
    app.component('Lab', Lab)
  },
}

