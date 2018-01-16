<template>
  <div>
    <h1>saved messages from new to old</h1>
    <ul>
      <li v-if="messages.length === 0"><i>no messages</i></li>
      <li v-for="message in messages">{{message}}</li>
    </ul>
    <button type="button" :disabled="offset == 0" @click="turnPage(-1)">&lt;&lt;</button>
    <button type="button" :disabled="!(offset + limit < total)" @click="turnPage(+1)">&gt;&gt;</button>

    <div class="grey">
      offset: {{offset}}
      limit: {{limit}}
      total: {{total}}
      paginationId: {{paginationId}}
    </div>
  </div>
</template>

<script>
export default {
  name: 'Saved',
  mounted () {
    this.load()
  },
  methods: {
    turnPage (direction) {
      this.offset += direction * this.limit
      this.load()
    },
    load () {
      var self = this
      self.$http.get(
        '/api/v1/messages/', { params: {
          offset: self.offset,
          limit: self.limit,
          paginationId: self.paginationId
        }}).then(function (response) {
          var data = response.body
          self.messages = data.messages
          self.offset = data.offset
          self.limit = data.limit
          self.paginationId = data.paginationId
          self.total = data.total
          self.error = ''
        }, function (error) {
          if (error.body.error) {
            self.error = error.body.description
          } else {
            self.error = error.bodyText
          }
        })
    }
  },
  data () {
    return {
      messages: [],
      paginationId: undefined,
      offset: 0,
      limit: 10,
      total: 0
    }
  }
}
</script>

<style>
</style>
