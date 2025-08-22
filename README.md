# RSS grátis para o Hedgepoint HUB (DIY c/ GitHub Pages)

Gera um **feed RSS** (feed.xml) com **o item mais recente** indexado para `site:hedgepointhub.com.br/blog`, atualizado **a cada 30 minutos** via **GitHub Actions**, e publicado no **GitHub Pages**.

## Como usar (sem custo)
1. **Crie um repositório público no GitHub** (ex.: `hedgepointhub-feed`).  
2. Faça **upload** destes arquivos na raiz:
   - `feed_builder.py`
   - `requirements.txt`
   - `.github/workflows/build.yml`
3. (Opcional) Em **Settings → Secrets → Actions**, crie `BING_API_KEY` (Azure Bing Web Search).  
   Sem essa chave, o script usa fallback via HTML do Bing (funciona, mas a data pode vir como N/D).
4. Vá em **Settings → Pages** e ative o GitHub Pages para a **branch `main`** (root).  
5. O workflow roda **a cada 30 min** e gera `feed.xml`.  
6. Seu feed ficará disponível em:  
   `https://<seu-usuario>.github.io/<repo>/feed.xml`

## Teste local (opcional)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python feed_builder.py
open feed.xml
```

## Observações
- Este feed **não é oficial** do Hedgepoint HUB; é gerado a partir do que os buscadores indexam.
- Se o buscador ainda não tiver indexado um relatório novo, ele não aparecerá no RSS de imediato.
- Para maior estabilidade, configure `BING_API_KEY` (Azure) nos Secrets do repositório.
- Você pode assinar o feed no HubSpot, Outlook, Slack, etc.
