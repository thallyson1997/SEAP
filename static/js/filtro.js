/* Adiciona campos de mês e ano para filtro na página index.html */

// Função para atualizar o link dos lotes conforme o filtro selecionado
function atualizarLinksLotes() {
    const mes = document.getElementById('filtro-mes').value;
    const ano = document.getElementById('filtro-ano').value;
    document.querySelectorAll('.card').forEach(card => {
        const lote = card.getAttribute('data-lote');
        if (lote) {
            card.href = `/lote1?mes=${mes}&ano=${ano}`;
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('filtro-mes').addEventListener('change', atualizarLinksLotes);
    document.getElementById('filtro-ano').addEventListener('change', atualizarLinksLotes);
    atualizarLinksLotes();
});
