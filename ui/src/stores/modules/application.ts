import { defineStore } from 'pinia'
const useApplicationStore = defineStore('application', {
  state: () => ({
    location: `${window.location.origin}${
      window.TelecomAI.chatPrefix ? window.TelecomAI.chatPrefix : window.TelecomAI.prefix
    }/`,
  }),
  actions: {},
})

export default useApplicationStore
