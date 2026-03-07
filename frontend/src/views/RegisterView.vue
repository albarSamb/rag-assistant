<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const localError = ref(null)

async function handleRegister() {
  localError.value = null
  if (password.value !== confirmPassword.value) {
    localError.value = 'Les mots de passe ne correspondent pas'
    return
  }
  if (password.value.length < 6) {
    localError.value = 'Le mot de passe doit contenir au moins 6 caracteres'
    return
  }
  const success = await auth.register(email.value, password.value, fullName.value)
  if (success) router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">DocuBot</h1>
        <p class="text-gray-500 mt-2">Creer votre compte</p>
      </div>

      <form @submit.prevent="handleRegister" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-5">
        <h2 class="text-xl font-semibold text-gray-900">Inscription</h2>

        <div v-if="localError || auth.error" class="bg-red-50 text-red-600 text-sm rounded-lg p-3">
          {{ localError || auth.error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nom complet</label>
          <input
            v-model="fullName"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="Albar SAMB"
          />
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
            placeholder="Min. 6 caracteres"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirmer le mot de passe</label>
          <input
            v-model="confirmPassword"
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
          {{ auth.loading ? 'Inscription...' : "S'inscrire" }}
        </button>

        <p class="text-center text-sm text-gray-500">
          Deja un compte ?
          <router-link to="/login" class="text-blue-600 hover:underline">Se connecter</router-link>
        </p>
      </form>
    </div>
  </div>
</template>
