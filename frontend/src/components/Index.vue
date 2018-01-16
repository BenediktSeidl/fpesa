<template>
  <div>
    <ul v-for="message in messages">
      <li :class="[message.class]"><div class="date">{{message.date}}:</div><pre>{{message.message|json}}</pre></li>
    </ul>
    <div v-show="numRemovedMessages > 0">
      ... and {{numRemovedMessages}} removed Messages
    </div>
  </div>
</template>

<script>
export default {
  name: 'Index',
  mounted () {
    var self = this
    self.insertMessage({class: 'internal', message: 'connection_status: offline'})
    self.init()
  },
  methods: {
    insertMessage (message) {
      message.date = (new Date()).toISOString()
      this.messages.unshift(message)
      if (this.messages.length > this.displayedMessages) {
        var numToRemoveMessages = this.messages.length-this.displayedMessages
        this.messages.splice(this.displayedMessages, numToRemoveMessages)
        this.numRemovedMessages += numToRemoveMessages
      }
    },
    onSocketOpen (event) {
      this.insertMessage({class: 'internal-success', message: 'connection_status: connected'})
      self.toWait = 1
    },
    onSocketClose (event) {
      var self = this
      self.insertMessage({class: 'internal', message: 'connection_status: closed (' + event.code + ')'})
      self.insertMessage({class: 'internal', message: 'trying to reconnect in ' + self.toWait + 's'})
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
        self.insertMessage({message: JSON.parse(event.target.result)})
      })
      reader.readAsText(event.data)
    },
    onSocketError (event) {
      this.insertMessage({class: 'internal-error', message: 'connection_status: error'})
    },
    init () {
      var self = this
      self.insertMessage({class: 'internal', message: 'connection_status: trying to connect...'})
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
      displayedMessages: 30,
      numRemovedMessages: 0,
      messages: []
    }
  }
}
</script>

<style scoped>
ul, li {
  list-style-type: none;
  margin: 0;
  padding: 0;
  width: 100%;
  float: left;
}
li { border-bottom: 1px dotted black; margin-bottom: 4px; padding-bottom: 4px;}
li.internal {color: #999;}
li.internal-error {color: #900;}
li.internal-success {color: #090;}

li div.date { float:left; margin-right: 3px;}
li pre { margin:0; padding:0; float: left;}

</style>
