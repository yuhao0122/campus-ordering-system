(function () {
  "use strict";

  function formatAmount(value) {
    return "NT$" + value.toLocaleString("zh-TW");
  }

  function parseQuantity(input) {
    var quantity = parseInt(input.value, 10);
    return Number.isFinite(quantity) && quantity >= 1 ? quantity : 1;
  }

  function recalculate() {
    var rows = document.querySelectorAll("[data-cart-row]");
    if (!rows.length) {
      return;
    }

    var total = 0;
    var merchantTotals = {};

    rows.forEach(function (row) {
      var unitPrice = parseInt(row.getAttribute("data-unit-price"), 10) || 0;
      var input = row.querySelector(".js-quantity");
      var quantity = input ? parseQuantity(input) : parseInt(row.getAttribute("data-quantity"), 10) || 1;
      var lineTotal = unitPrice * quantity;

      row.setAttribute("data-quantity", String(quantity));

      var lineSubtotal = row.querySelector(".js-line-subtotal");
      if (lineSubtotal) {
        lineSubtotal.textContent = formatAmount(lineTotal);
      }

      total += lineTotal;

      var merchantGroup = row.getAttribute("data-merchant-group");
      if (merchantGroup) {
        merchantTotals[merchantGroup] = (merchantTotals[merchantGroup] || 0) + lineTotal;
      }
    });

    document.querySelectorAll("[data-cart-total]").forEach(function (element) {
      element.textContent = formatAmount(total);
    });

    document.querySelectorAll("[data-merchant-subtotal]").forEach(function (element) {
      var merchantGroup = element.getAttribute("data-merchant-subtotal");
      if (merchantTotals[merchantGroup] !== undefined) {
        element.textContent = formatAmount(merchantTotals[merchantGroup]);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".js-quantity").forEach(function (input) {
      input.addEventListener("input", recalculate);
      input.addEventListener("change", recalculate);
    });

    recalculate();
  });
})();
