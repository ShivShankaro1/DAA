document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.algo-card');
  const algoInput = document.getElementById('algorithm');
  const compareBtn = document.getElementById('compareBtn');
  let selectedKey = algoInput ? algoInput.value : 'dp';

  // Function to handle selecting algo
  function setActive(key) {
    cards.forEach(card => {
      if (card.dataset.key === key) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });
    if (algoInput) algoInput.value = key;
    selectedKey = key;
  }

  // Click event for each algo card
  cards.forEach(card => {
    card.addEventListener('click', () => {
      setActive(card.dataset.key);
    });
  });

  // Default active state for first card
  if (cards.length && !selectedKey) {
    setActive(cards[0].dataset.key);
  }

  // Compare All Algorithms
  if (compareBtn) {
    compareBtn.addEventListener('click', () => {
      const form = document.querySelector('form[action="/result"]');
      if (!form) {
        alert("Form not found!");
        return;
      }

      const capacityInput = form.querySelector('input[name="capacity"]');
      const capacityValue = capacityInput ? capacityInput.value : 0;

      if (!capacityValue || isNaN(capacityValue)) {
        alert("Please enter a valid capacity before comparing algorithms.");
        return;
      }

      const tempForm = document.createElement('form');
      tempForm.method = 'POST';
      tempForm.action = '/compare';

      const capField = document.createElement('input');
      capField.type = 'hidden';
      capField.name = 'capacity';
      capField.value = capacityValue;
      tempForm.appendChild(capField);

      document.body.appendChild(tempForm);
      tempForm.submit();
    });
  }

  // ✅ Sync pie & bar chart colors
  if (typeof Chart !== 'undefined' && window.barChart && window.pieChart) {
    const barColors = window.barChart.data.datasets[0].backgroundColor;
    window.pieChart.data.datasets[0].backgroundColor = barColors;
    window.pieChart.update();
  }
});
