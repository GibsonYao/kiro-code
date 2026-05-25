<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { setupRouteGuard } from '@/utils/route-guard'

onLaunch(() => {
  console.log('App Launch')
  setupRouteGuard()
})

onShow(() => {
  console.log('App Show')
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
@import './styles/global.scss';
</style>
