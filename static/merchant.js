/**
 * Merchant products UI — B-US01, B-US02, B-US03, B-US04.
 * Real mode calls GET/POST /api/products; no database is created here.
 * Preview mode: merchant.html?demo=1, or open this HTML with file://.
 * Preview writes to memory only and is reset on refresh.
 */
(() => {
  'use strict';

  const form = document.getElementById('productForm');
  if (!form) return;

  const els = {
    name: document.getElementById('productName'),
    price: document.getElementById('productPrice'),
    nameError: document.getElementById('nameError'),
    priceError: document.getElementById('priceError'),
    formMessage: document.getElementById('formMessage'),
    listMessage: document.getElementById('listMessage'),
    body: document.getElementById('productTableBody'),
    count: document.getElementById('productCount'),
    loading: document.getElementById('loadingState'),
    empty: document.getElementById('emptyState'),
    tableWrap: document.getElementById('tableWrap'),
    submit: document.getElementById('submitButton'),
    refresh: document.getElementById('refreshButton'),
    demoBanner: document.getElementById('demoBanner'),
  };

  const params = new URLSearchParams(window.location.search);
  const isDemo = params.get('demo') === '1' || window.location.protocol === 'file:';
  const priceFormatter = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 0 });
  let mockProducts = [
    { id: 1, name: '雞腿便當', price: 85, is_active: true },
    { id: 2, name: '排骨便當', price: 90, is_active: true },
  ];
  let isSubmitting = false;

  els.demoBanner.hidden = !isDemo;
  const ordersLink = document.getElementById('ordersLink');
  if (ordersLink && isDemo) ordersLink.href = 'merchant_orders.html?demo=1';

  function message(target, text, kind) {
    target.textContent = text;
    target.dataset.kind = kind;
    target.hidden = !text;
  }

  function fieldError(input, errorNode, text) {
    input.setAttribute('aria-invalid', String(Boolean(text)));
    errorNode.textContent = text;
    errorNode.hidden = !text;
  }

  function validate() {
    const name = els.name.value.trim();
    const rawPrice = els.price.value.trim();
    const chars = Array.from(name).length;
    let nameError = '';
    let priceError = '';

    if (!name) nameError = '請輸入商品名稱。';
    else if (chars > 100) nameError = '商品名稱最多 100 個字。';

    // Digits only: no 0, negatives, decimals, scientific notation or spaces.
    if (!/^[0-9]+$/.test(rawPrice)) priceError = '價格必須是大於 0 的整數。';
    const price = Number(rawPrice);
    if (!priceError && (!Number.isSafeInteger(price) || price <= 0)) {
      priceError = '價格必須是大於 0 的安全整數。';
    }

    fieldError(els.name, els.nameError, nameError);
    fieldError(els.price, els.priceError, priceError);
    return nameError || priceError ? null : { name, price };
  }

  async function requestApi(method, path, payload) {
    if (isDemo) {
      if (method === 'GET' && path === '/api/products') {
        return mockProducts.map((product) => ({ ...product }));
      }
      if (method === 'POST' && path === '/api/products') {
        const nextId = Math.max(0, ...mockProducts.map((product) => product.id)) + 1;
        const saved = { id: nextId, ...payload, is_active: true };
        mockProducts.push(saved);
        return { ...saved };
      }
      throw new Error('示範模式不支援這個 API。');
    }

    let response;
    try {
      response = await fetch(path, {
        method,
        headers: { Accept: 'application/json', ...(payload ? { 'Content-Type': 'application/json' } : {}) },
        ...(payload ? { body: JSON.stringify(payload) } : {}),
      });
    } catch (_) {
      throw new Error('無法連線至伺服器。請確認 Flask 已啟動且 API 已整合。');
    }

    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(`伺服器回應格式錯誤（HTTP ${response.status}）。`);
    }

    if (!response.ok) {
      const text = data && typeof data.error === 'string' ? data.error : '請稍後再試。';
      throw new Error(`${text}（HTTP ${response.status}）`);
    }
    if (method === 'POST' && response.status !== 201) {
      throw new Error(`新增商品應回傳 HTTP 201，實際為 ${response.status}。`);
    }
    return data;
  }

  function appendCell(row, value, extraClass = '') {
    const td = document.createElement('td');
    if (extraClass) td.className = extraClass;
    td.textContent = value;
    row.appendChild(td);
    return td;
  }

  function renderProducts(products) {
    if (!Array.isArray(products)) throw new Error('商品 API 應回傳 JSON 陣列。');
    els.body.replaceChildren();

    for (const product of products) {
      if (typeof product.name !== 'string' || !Number.isSafeInteger(product.price)) {
        throw new Error('商品資料格式不符合 API 契約。');
      }
      const tr = document.createElement('tr');
      appendCell(tr, product.name);
      appendCell(tr, `NT$${priceFormatter.format(product.price)}`, 'right');
      const statusCell = document.createElement('td');
      statusCell.className = 'right';
      const statusLabel = document.createElement('span');
      const isActive = product.is_active === true || product.is_active === 1;
      statusLabel.className = `state ${isActive ? 'active' : 'inactive'}`;
      statusLabel.textContent = isActive ? '上架中' : '已下架';
      statusCell.appendChild(statusLabel);
      tr.appendChild(statusCell);
      els.body.appendChild(tr);
    }

    els.count.textContent = `共 ${products.length} 項商品`;
    els.empty.hidden = products.length !== 0;
    els.tableWrap.hidden = products.length === 0;
  }

  async function loadProducts() {
    els.loading.hidden = false;
    els.empty.hidden = true;
    els.tableWrap.hidden = true;
    els.refresh.disabled = true;
    message(els.listMessage, '', 'error');
    try {
      const products = await requestApi('GET', '/api/products');
      renderProducts(products);
    } catch (error) {
      els.count.textContent = '無法讀取商品';
      message(els.listMessage, error.message || '商品讀取失敗。', 'error');
    } finally {
      els.loading.hidden = true;
      els.refresh.disabled = false;
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (isSubmitting) return;
    message(els.formMessage, '', 'error');
    const data = validate();
    if (!data) {
      (els.name.getAttribute('aria-invalid') === 'true' ? els.name : els.price).focus();
      return;
    }
    isSubmitting = true;
    els.submit.disabled = true;
    els.submit.textContent = '新增中…';
    try {
      const saved = await requestApi('POST', '/api/products', data);
      if (!saved || !Number.isInteger(saved.id)) {
        throw new Error('伺服器未回傳新增商品的有效 ID。');
      }
      form.reset();
      fieldError(els.name, els.nameError, '');
      fieldError(els.price, els.priceError, '');
      message(els.formMessage, `商品「${saved.name}」新增成功！`, 'success');
      await loadProducts();
    } catch (error) {
      message(els.formMessage, error.message || '新增商品失敗。', 'error');
    } finally {
      isSubmitting = false;
      els.submit.disabled = false;
      els.submit.textContent = '新增商品';
    }
  });

  els.refresh.addEventListener('click', loadProducts);
  els.name.addEventListener('input', () => fieldError(els.name, els.nameError, ''));
  els.price.addEventListener('input', () => fieldError(els.price, els.priceError, ''));
  loadProducts();
})();

/**
 * Merchant orders UI — B-US05, B-US06.
 * Actual source: GET /api/merchant/orders, owned by the integrated Flask backend.
 * Preview: merchant_orders.html?demo=1 or file:// (fixed sample data only).
 * No payment update, database changes, or new endpoints are implemented here.
 */
(() => {
  'use strict';

  const listNode = document.getElementById('ordersList');
  if (!listNode) return;

  const els = {
    banner: document.getElementById('ordersDemoBanner'),
    link: document.getElementById('productsLink'),
    count: document.getElementById('ordersCount'),
    refresh: document.getElementById('ordersRefreshButton'),
    loading: document.getElementById('ordersLoading'),
    empty: document.getElementById('ordersEmpty'),
    error: document.getElementById('ordersError'),
  };
  const query = new URLSearchParams(window.location.search);
  const demo = query.get('demo') === '1' || window.location.protocol === 'file:';
  const money = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 0 });
  const mockOrders = [
    {
      id: 1001,
      total_amount: 170,
      payment_status: 'unpaid',
      created_at: '2026-11-05 11:25:00',
      items: [{ product_name: '雞腿便當', unit_price: 85, quantity: 2, subtotal: 170 }],
    },
    {
      id: 1002,
      total_amount: 90,
      payment_status: 'paid',
      created_at: '2026-11-05 12:02:00',
      items: [{ product_name: '排骨便當', unit_price: 90, quantity: 1, subtotal: 90 }],
    },
  ];

  els.banner.hidden = !demo;
  if (demo) els.link.href = 'merchant.html?demo=1';

  function formatMoney(amount) {
    return `NT$${money.format(amount)}`;
  }
  function td(row, content, right = false) {
    const cell = document.createElement('td');
    cell.textContent = String(content);
    if (right) cell.className = 'right';
    row.appendChild(cell);
  }
  function validateOrder(order) {
    if (!order || !Number.isSafeInteger(order.id) || order.id < 1 ||
        !Number.isSafeInteger(order.total_amount) || order.total_amount < 0 ||
        (order.payment_status !== 'paid' && order.payment_status !== 'unpaid') ||
        typeof order.created_at !== 'string' || !Array.isArray(order.items)) {
      throw new Error('訂單資料不符合 API 契約，請聯繫後端開發者確認。');
    }
    for (const item of order.items) {
      if (!item || typeof item.product_name !== 'string' ||
          !Number.isSafeInteger(item.unit_price) || item.unit_price < 0 ||
          !Number.isSafeInteger(item.quantity) || item.quantity < 1 ||
          !Number.isSafeInteger(item.subtotal) || item.subtotal < 0) {
        throw new Error(`訂單 #${order.id} 的商品明細格式不正確。`);
      }
    }
  }
  function render(orders) {
    if (!Array.isArray(orders)) throw new Error('訂單 API 應回傳 JSON 陣列。');
    orders.forEach(validateOrder);
    listNode.replaceChildren();
    els.count.textContent = `（共 ${orders.length} 筆）`;
    els.empty.hidden = orders.length !== 0;
    listNode.hidden = orders.length === 0;
    for (const order of orders) {
      const card = document.createElement('article');
      card.className = 'order-card';
      const head = document.createElement('div');
      head.className = 'order-head';
      const heading = document.createElement('div');
      const orderId = document.createElement('div');
      orderId.className = 'order-id';
      orderId.textContent = `訂單 #${order.id}`;
      const createdAt = document.createElement('div');
      createdAt.className = 'order-time';
      createdAt.textContent = `建立時間：${order.created_at}`;
      heading.append(orderId, createdAt);
      const status = document.createElement('span');
      status.className = `state ${order.payment_status}`;
      status.textContent = order.payment_status === 'paid' ? '已付款（模擬）' : '未付款';
      head.append(heading, status);

      const tableWrap = document.createElement('div');
      tableWrap.className = 'table-wrap';
      const table = document.createElement('table');
      table.className = 'orders-table';
      const thead = document.createElement('thead');
      const trHead = document.createElement('tr');
      for (const title of ['商品', '單價', '數量', '小計']) {
        const th = document.createElement('th');
        th.scope = 'col';
        th.textContent = title;
        if (title !== '商品') th.className = 'right';
        trHead.appendChild(th);
      }
      thead.appendChild(trHead);
      const tbody = document.createElement('tbody');
      for (const item of order.items) {
        const tr = document.createElement('tr');
        td(tr, item.product_name);
        td(tr, formatMoney(item.unit_price), true);
        td(tr, item.quantity, true);
        td(tr, formatMoney(item.subtotal), true);
        tbody.appendChild(tr);
      }
      table.append(thead, tbody);
      tableWrap.appendChild(table);
      const total = document.createElement('div');
      total.className = 'order-total';
      const label = document.createElement('span');
      label.textContent = '訂單總額';
      const amount = document.createElement('strong');
      amount.textContent = formatMoney(order.total_amount);
      total.append(label, amount);
      card.append(head, tableWrap, total);
      listNode.appendChild(card);
    }
  }

  async function load() {
    els.refresh.disabled = true;
    els.loading.hidden = false;
    els.empty.hidden = true;
    listNode.hidden = true;
    els.error.hidden = true;
    els.error.textContent = '';
    try {
      let orders;
      if (demo) {
        orders = mockOrders;
      } else {
        let response;
        try {
          response = await fetch('/api/merchant/orders', { headers: { Accept: 'application/json' } });
        } catch (_) {
          throw new Error('無法連線至伺服器。請確認 Flask 已啟動且訂單 API 已整合。');
        }
        let data;
        try {
          data = await response.json();
        } catch (_) {
          throw new Error(`伺服器回應格式錯誤（HTTP ${response.status}）。`);
        }
        if (!response.ok) {
          const errorText = data && typeof data.error === 'string' ? data.error : '訂單讀取失敗。';
          throw new Error(`${errorText}（HTTP ${response.status}）`);
        }
        orders = data;
      }
      render(orders);
    } catch (error) {
      els.count.textContent = '（無法載入）';
      listNode.replaceChildren();
      els.error.textContent = error.message || '訂單讀取失敗。';
      els.error.hidden = false;
    } finally {
      els.loading.hidden = true;
      els.refresh.disabled = false;
    }
  }

  els.refresh.addEventListener('click', load);
  load();
})();
