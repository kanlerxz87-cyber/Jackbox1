const form = document.getElementById('calc');
if (form) {
  const result = document.getElementById('result');
  form.addEventListener('submit', event => {
    event.preventDefault();
    const fields = ['price', 'cost', 'debt', 'saleTax', 'hold', 'holdTax'];
    const values = fields.map(name => form.elements[name]);
    if (values.some(field => field.value.trim() === '' || !field.validity.valid || !Number.isFinite(field.valueAsNumber))) {
      result.textContent = 'Enter a valid number in every field before calculating.';
      return;
    }
    const [price, cost, debt, saleTax, hold, holdTax] = values.map(field => field.valueAsNumber);
    const saleNet = price - cost - debt - saleTax;
    const holdNet = hold - holdTax;
    const money = value => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:2}).format(value);
    result.textContent = `Illustrative sale net: ${money(saleNet)} · Hold after-tax present value: ${money(holdNet)} · Sale minus hold: ${money(saleNet - holdNet)}. These figures depend entirely on your inputs and are not a recommendation.`;
  });
  form.addEventListener('reset', () => { result.textContent = 'No comparison calculated. Verified inputs are missing.'; });
}
