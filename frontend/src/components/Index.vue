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
    // TODO: add time?
    self.messages.unshift({class: 'internal', message: 'connection_status: offline'})
    self.init()
  },
  methods: {
    onSocketOpen (event) {
      this.messages.unshift({class: 'internal', message: 'connection_status: connected'})
      self.toWait = 1
    },
    onSocketClose (event) {
      var self = this
      self.messages.unshift({class: 'internal', message: 'connection_status: closed'})
      self.messages.unshift({class: 'internal', message: 'trying to reconnect in ' + self.toWait + 's'})
      self.socket.removeEventListener('open', self.onSocketOpen)
      self.socket.removeEventListener('close', self.onSocketClose)
      self.socket.removeEventListener('error', self.onSocketError)
      self.socket.removeEventListener('message', self.onSocketMessage)
      setTimeout(function () {
        self.init()
        self.toWait *= 2
      }, self.toWait * 1000)
    },
    onSocketMessage (event) {
      var self = this
      var reader = new FileReader()
      reader.addEventListener('load', function (event) {
        self.messages.unshift({message: JSON.parse(event.target.result)})
      })
      reader.readAsText(event.data)
    },
    onSocketError (event) {
      this.messages.unshift({class: 'internal-error', message: 'connection_status: error ' + event})
    },
    init () {
      var self = this
      self.messages.unshift({class: 'internal', message: 'connection_status: trying to connect...'})
      self.socket = new WebSocket('ws://' + location.host + '/ws/v1/')
      self.socket.addEventListener('open', self.onSocketOpen)
      self.socket.addEventListener('close', self.onSocketClose)
      self.socket.addEventListener('error', self.onSocketError)
      self.socket.addEventListener('message', self.onSocketMessage)
    }
  },
  data () {
    return {
      toWait: 1,
      messages: []
    }
  }
}
</script>

<style scoped>
</style>
