import os
import sys
from typing import Any
try:
	# Carrega variáveis do arquivo .env se existir
	from dotenv import load_dotenv  # type: ignore[import-not-found]
	load_dotenv()
except Exception:
	# Se python-dotenv não estiver instalado, apenas seguimos sem falhar.
	# As variáveis ainda podem vir do ambiente do sistema.
	pass
try:
	import google.generativeai as genai  # type: ignore[import-not-found]
except Exception as exc:
	print("Erro: o pacote 'google-generativeai' não está instalado ou falhou ao importar.")
	print("Instale com: pip install google-generativeai")
	print(f"Detalhes: {exc}")
	sys.exit(1)

def _get_api_key() -> str:
	"""Obtém a chave da API do Gemini da variável de ambiente GEMINI_API_KEY.
	Encerra com mensagem amigável se não estiver definida.
	"""
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		print("Erro: variável de ambiente GEMINI_API_KEY não definida.")
		print("Opções para configurar:")
		print("  1) Crie um arquivo .env na raiz do projeto com a linha:")
		print("     GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI")
		print("     (Opcional: GEMINI_MODEL=gemini-1.5-flash)")
		print("  2) OU defina no PowerShell da sessão atual:")
		print("     $env:GEMINI_API_KEY = 'COLE_SUA_CHAVE_AQUI'")
		print("  3) OU defina de forma persistente:")
		print("     setx GEMINI_API_KEY \"COLE_SUA_CHAVE_AQUI\"")
		sys.exit(1)
	return api_key

def _list_available_models() -> list[str]:
	"""Retorna a lista de modelos disponíveis para esta chave/conta.
	Se falhar, retorna lista vazia.
	"""
	try:
		models: Any = genai.list_models()  # type: ignore[attr-defined]
		names: list[str] = []
		for m in models:  # type: ignore
			# Alguns retornam m.name como 'models/<id>' — preservamos o que vier
			from typing import cast as _cast
			mm: Any = _cast(Any, m)
			names.append(getattr(mm, "name", ""))
		return [n for n in names if n]
	except Exception:
		return []

def _choose_model_name(preferred: str | None) -> str:
	"""Escolhe um modelo suportado. Prioriza a env var, depois candidatos comuns,
	e, por fim, faz fallback para o primeiro modelo com suporte.
	"""
	# Ordem de tentativa comum (pode variar por região/conta)
	candidates = [
		"gemini-1.5-flash-latest",
		"gemini-1.5-flash",
		"gemini-1.5-flash-8b",
		"gemini-1.5-pro-latest",
		"gemini-1.5-pro",
	]

	available = _list_available_models()
	# Normalizar para comparar tanto 'gemini-...' quanto 'models/gemini-...'
	normalized_available = set(a.split("/")[-1] for a in available)

	if preferred:
		# aceita tanto 'gemini-...' quanto 'models/gemini-...'
		pref_norm = preferred.split("/")[-1]
		if not available or pref_norm in normalized_available:
			return preferred

	# Tenta candidatos comuns que apareçam na lista
	if available:
		for c in candidates:
			if c.split("/")[-1] in normalized_available:
				return c
		# Como fallback, usa o primeiro disponível
		return available[0]

	# Se não conseguimos listar (falha de rede/escopo), tenta candidatos fixos
	return preferred or candidates[0]

def main() -> None:
	# Configurar a chave da API de forma segura (via variável de ambiente)
	genai.configure(api_key=_get_api_key())  # type: ignore[attr-defined]

	# Permitir configurar o modelo via variável de ambiente (padrão atualizado)
	env_model = os.getenv("GEMINI_MODEL")
	chosen_model = _choose_model_name(env_model or "gemini-1.5-flash-latest")
	model: Any = genai.GenerativeModel(chosen_model)  # type: ignore[attr-defined]

	# Integração com o serviço bancário
	try:
		from bank_service import BankApp, help_text
	except Exception as exc:
		print(f"Falha ao importar serviço bancário: {exc}")
		sys.exit(1)

	bank = BankApp()

	# Mensagem de boas-vindas e dicas de uso
	print("\nAssistente bancário iniciado. Digite mensagens para conversar.")
	print("Use comandos começando com '/' para realizar ações. Digite /help para ver opções.\n")

	# Prompt de sistema para orientar o tom do chatbot
	system_prompt = (
		"Você é um assistente bancário amigável e objetivo. Responda em português brasileiro. "
		"Quando o usuário executar comandos (ex: /depositar 100), não repita os detalhes técnicos; "
		"apenas confirme o resultado de forma clara e ofereça ajuda adicional."
	)

	history: list[dict[str, Any]] = [
		{"role": "user", "parts": [system_prompt]},
	]

	def chat_answer(text: str) -> None:
		try:
			history.append({"role": "user", "parts": [text]})
			resp = model.generate_content(history)  # type: ignore[attr-defined]
			answer = getattr(resp, "text", str(resp))
			print(answer)
			history.append({"role": "model", "parts": [answer]})
		except Exception as exc:
			print(f"Falha ao gerar resposta do assistente: {exc}")
			avail = _list_available_models()
			if avail:
				print("Modelos disponíveis para sua chave:")
				for name in avail:
					print(f"  - {name}")
				print("Dica: defina GEMINI_MODEL com um dos nomes acima e rode novamente.")
			else:
				print("Não foi possível obter a lista de modelos.")

	def parse_float(s: str) -> float:
		try:
			return float(s.replace(",", "."))
		except Exception:
			raise ValueError("Valor numérico inválido.")

	# Loop principal do chat
	while True:
		try:
			user = input("> ").strip()
		except (KeyboardInterrupt, EOFError):
			print("\nAté mais!")
			break

		if not user:
			continue
		if user.lower() in {"/exit", "/sair", "exit", "sair"}:
			print("Até mais!")
			break

		if user.startswith("/"):
			parts = user.split()
			cmd = parts[0].lower()
			args = parts[1:]
			msg = ""
			try:
				if cmd in {"/help", "/ajuda"}:
					msg = help_text()
				elif cmd == "/login":
					if not args:
						msg = "Uso: /login <cpf> (somente números)."
					else:
						msg = bank.login(args[0])
				elif cmd == "/logout":
					msg = bank.logout()
				elif cmd == "/novo_usuario":
					# coleta interativa de dados
					cpf = input("CPF (somente números): ").strip()
					nome = input("Nome completo: ").strip()
					nasc = input("Data nascimento (dd/mm/aaaa): ").strip()
					end  = input("Endereço (logradouro, nr - bairro - cidade/UF): ").strip()
					msg = bank.novo_usuario(nome=nome, cpf=cpf, data_nascimento=nasc, endereco=end)
				elif cmd == "/nova_conta":
					msg = bank.nova_conta()
				elif cmd == "/saldo":
					msg = bank.saldo()
				elif cmd == "/extrato":
					msg = bank.extrato()
				elif cmd == "/depositar":
					if not args:
						msg = "Uso: /depositar <valor>"
					else:
						val = parse_float(args[0])
						msg = bank.depositar(val)
				elif cmd == "/sacar":
					if not args:
						msg = "Uso: /sacar <valor>"
					else:
						val = parse_float(args[0])
						msg = bank.sacar(val)
				elif cmd == "/simular_emprestimo":
					if len(args) < 3:
						msg = "Uso: /simular_emprestimo <valor> <parcelas> <taxa> (ex: 5000 12 0.02)"
					else:
						valor = parse_float(args[0])
						parcelas = int(args[1])
						taxa = parse_float(args[2])
						msg = bank.simular_emprestimo(valor, parcelas, taxa)
				elif cmd == "/contratar_emprestimo":
					if len(args) < 3:
						msg = "Uso: /contratar_emprestimo <valor> <parcelas> <taxa>"
					else:
						valor = parse_float(args[0])
						parcelas = int(args[1])
						taxa = parse_float(args[2])
						msg = bank.contratar_emprestimo(valor, parcelas, taxa)
				elif cmd == "/pagar_parcela":
					msg = bank.pagar_parcela()
				elif cmd == "/quitar_emprestimo":
					msg = bank.quitar_emprestimo()
				else:
					msg = "Comando não reconhecido. Use /help."
			except ValueError as ve:
				msg = f"Erro: {ve}"
			except Exception as exc:
				msg = f"Erro ao executar comando: {exc}"

			print(msg)
			# Opcional: peça ao modelo para responder cordialmente ao resultado
			chat_answer(f"Resumo da ação para o cliente: {msg}")
			continue

		# Mensagem normal: conversa com o assistente
		chat_answer(user)

if __name__ == "__main__":
	main()
