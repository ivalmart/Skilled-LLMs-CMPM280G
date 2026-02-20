client<llm> SMALL_MODEL {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "z-ai/glm-5"
    request_timeout 120
  }
}
