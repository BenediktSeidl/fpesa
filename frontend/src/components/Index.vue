<template>
  <div>
    <ul v-for="message in messages">
        <li>{{message}}</li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Index',
  mounted () {
    var self = this
    // TODO: don't push but insert at pos 0 so we don't have to scroll
    // TODO: add time?
    self.messages.push({class: 'internal', message: 'connection_status: offline'})
    self.init()
  },
  methods: {
    onSocketOpen (event) {
      this.messages.push({class: 'internal', message: 'connection_status: connected'})
    },
    onSocketClose (event) {
      var self = this
      self.messages.push({class: 'internal', message: 'connection_status: closed'})
      self.messages.push({class: 'internal', message: 'trying to reconnect'})
      self.socket.removeEventListener('open', self.onSocketOpen)
      self.socket.removeEventListener('close', self.onSocketClose)
      self.socket.removeEventListener('error', self.onSocketError)
      self.socket.removeEventListener('message', self.onSocketMessage)
      setTimeout(function () {
        self.init()
      }, 1000)
    },
    onSocketMessage (event) {
      this.messages.push({message: event.data})
    },
    onSocketError (event) {
      this.messages.push({class: 'internal-error', message: 'connection_status: error ' + event})
    },
    init () {
      var self = this
      self.messages.push({class: 'internal', message: 'connection_status: trying to connect...'})
      self.socket = new WebSocket('ws://' + location.host + '/ws/v1/')
      self.socket.addEventListener('open', self.onSocketOpen)
      self.socket.addEventListener('close', self.onSocketClose)
      self.socket.addEventListener('error', self.onSocketError)
      self.socket.addEventListener('message', self.onSocketMessage)
    }
  },
  data () {
    return {
      messages: []
    }
  }
}
</script>

<style scoped>
</style>
