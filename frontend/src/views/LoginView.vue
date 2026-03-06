<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')

async function handleLogin() {
  const success = await auth.login(email.value, password.value)
  if (success) router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">DocuBot</h1>
        <p class="text-gray-500 mt-2">Assistant Documentation Technique</p>
      </div>

      <form @submit.prevent="handleLogin" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-5">
        <h2 class="text-xl font-semibold text-gray-900">Connexion</h2>

        <div v-if="auth.error" class="bg-red-50 text-red-600 text-sm rounded-lg p-3">
          {{ auth.error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="vous@exemple.com"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="********"
          />
        </div>

        <button
          type="submit"
          :disabled="auth.loading"
          class="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ auth.loading ? 'Connexion...' : 'Se connecter' }}
        </button>

        <p class="text-center text-sm text-gray-500">
          Pas de compte ?
          <router-link to="/register" class="text-blue-600 hover:underline">Creer un compte</router-link>
        </p>
      </form>
    </div>
  </div>
</template>
