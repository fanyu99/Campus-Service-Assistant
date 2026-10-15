import { ref } from 'vue'

const hoverMessage = ref<string | null>(null)

export function useCharacterBubble() {
  function setHoverMessage(message: string) {
    hoverMessage.value = message
  }

  function clearHoverMessage() {
    hoverMessage.value = null
  }

  return { hoverMessage, setHoverMessage, clearHoverMessage }
}

