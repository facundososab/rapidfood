// POS cliente-side: lee sus datos desde bloques json_script y expone dos
// componentes Alpine. Sin interpolación de plantillas Django en JavaScript.
(function () {
  function readJSON(id, fallback) {
    const el = document.getElementById(id);
    if (!el) return fallback;
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      console.error('Invalid JSON in #' + id, err);
      return fallback;
    }
  }

  function fmt(v) {
    if (!v && v !== 0) return '—';
    const [w, f] = Number(v).toFixed(2).split('.');
    return '$ ' + w.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + f;
  }

  document.addEventListener('alpine:init', () => {
    Alpine.data('pos', () => ({
      products: readJSON('pos-products', []),
      clients: readJSON('pos-clients', []),
      config: readJSON('pos-config', {}),
      q: '',
      cat: '',
      cart: {},
      delivery: 'PICKUP',
      payment: 'CASH',
      clientQ: '',
      clientId: '',
      openClients: false,
      modal: false,
      quote: null,
      quoting: false,
      addr: { street: '', street_number: '', floor: '', apartment: '', city: '', province: '', postal_code: '' },
      couponCode: '',
      coupon: null,
      couponMsg: '',
      newClientOpen: false,
      newClientName: '',
      newClientLast: '',
      newClientPhone: '',
      newClientMsg: '',

      get shipping() {
        // Only the real quoted cost counts; before quoting there is no number.
        return this.quote && this.quote.available && this.quote.shipping_cost !== undefined
          ? Number(this.quote.shipping_cost)
          : 0;
      },

      get quoteReady() {
        return this.quote !== null && this.quote.available === true;
      },

      get hasClient() {
        return !!this.clientId || (this.clientQ || '').trim() !== '';
      },

      get clientMissing() {
        return this.items().length > 0 && !this.hasClient;
      },

      get minOrder() {
        return Number(this.config.minOrder || 0);
      },

      get belowMinimum() {
        // Minimum order applies to delivery only.
        return this.delivery === 'DELIVERY' && this.items().length > 0
          && this.minOrder > 0 && this.subtotal() < this.minOrder;
      },

      get missingForMinimum() {
        return Math.max(0, this.minOrder - this.subtotal());
      },

      canConfirm() {
        if (!this.items().length) return false;
        if (!this.hasClient) return false;
        if (this.belowMinimum) return false;
        if (this.delivery === 'DELIVERY') return this.quoteReady;
        return true;
      },

      setDelivery(kind) {
        if (this.delivery === kind) return;
        this.delivery = kind;
        this.quote = null;
      },

      resetQuote() {
        this.quote = null;
      },

      async requestQuote() {
        this.quoting = true;
        try {
          const body = new URLSearchParams(this.addr).toString();
          const res = await fetch('/pedidos/cotizacion/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body,
          });
          this.quote = await res.json();
        } catch (e) {
          this.quote = { available: false, error: 'No se pudo calcular el envío.' };
        } finally {
          this.quoting = false;
        }
      },

      filtered() {
        if (!this.cat) return this.products;
        return this.products.filter((p) => p.categoryId === this.cat);
      },

      clientResults() {
        const t = this.clientQ.trim().toLowerCase();
        if (!t) return this.clients.slice(0, 5);
        return this.clients
          .filter((c) => (c.name + ' ' + c.lastName + ' ' + c.phoneNumber).toLowerCase().includes(t))
          .slice(0, 5);
      },

      pickClient(c) {
        this.clientId = c.id;
        this.clientQ = c.name + ' ' + c.lastName;
        this.openClients = false;
      },

      toggleNewClient() {
        if (!this.newClientOpen) {
          if (!this.newClientName && this.clientQ) {
            const parts = this.clientQ.trim().split(' ');
            this.newClientName = parts[0] || '';
            this.newClientLast = parts.slice(1).join(' ');
          }
          this.openClients = false;
        }
        this.newClientMsg = '';
        this.newClientOpen = !this.newClientOpen;
      },

      cancelNewClient() {
        this.newClientOpen = false;
        this.newClientMsg = '';
        this.newClientName = '';
        this.newClientLast = '';
        this.newClientPhone = '';
      },

      async createClient() {
        const name = (this.newClientName || '').trim();
        const lastName = (this.newClientLast || '').trim();
        const phone = (this.newClientPhone || '').trim();
        if (!name || !phone) {
          this.newClientMsg = 'Completá nombre y teléfono.';
          return;
        }
        try {
          const res = await fetch('/pedidos/cliente/crear/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ name, last_name: lastName, phone }).toString(),
          });
          const data = await res.json();
          if (!data.ok) {
            this.newClientMsg = data.error || 'No se pudo crear el cliente.';
            return;
          }
          this.clients.push(data.client);
          this.pickClient(data.client);
          this.cancelNewClient();
        } catch (e) {
          this.newClientMsg = 'No se pudo crear el cliente.';
        }
      },

      openConfigModal(productId) {
        document.querySelectorAll('[data-order-modal]').forEach((m) => m.remove());
        const url = String(this.config.productConfigUrl || '').replace('0000', productId);
        fetch(url)
          .then((res) => {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.text();
          })
          .then((html) => {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = html;
            wrapper.setAttribute('data-order-modal', '');
            document.body.appendChild(wrapper);
          })
          .catch((e) => console.error('Error al abrir modal', e));
      },

      handleAddItem(detail) {
        const configId = [
          detail.productId,
          detail.variantId,
          [...detail.options].sort().join(','),
          [...detail.removedIngredients].sort().join(','),
        ].join('|');
        if (this.cart[configId]) {
          this.cart[configId].qty += detail.qty;
        } else {
          const p = this.products.find((x) => x.id === detail.productId) || {};
          this.cart[configId] = { ...detail, configId, image: p.imageUrl };
        }
      },

      add(configId) {
        if (this.cart[configId]) this.cart[configId].qty++;
      },
      dec(configId) {
        if (this.cart[configId] && this.cart[configId].qty > 1) this.cart[configId].qty--;
        else this.remove(configId);
      },
      remove(configId) {
        delete this.cart[configId];
      },
      items() {
        return Object.values(this.cart).map((i) => ({ ...i, subtotal: (i.price || 0) * i.qty }));
      },
      subtotal() {
        return this.items().reduce((s, i) => s + i.subtotal, 0);
      },
      discount() {
        return this.coupon && this.coupon.valid ? Number(this.coupon.discount_amount || 0) : 0;
      },
      total() {
        const shipping = this.delivery === 'DELIVERY' ? this.shipping : 0;
        return Math.max(0, this.subtotal() - this.discount() + shipping);
      },
      async applyCoupon() {
        const code = (this.couponCode || '').trim();
        if (!code) { this.coupon = null; this.couponMsg = ''; return; }
        try {
          const res = await fetch('/pedidos/cupon/validar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ coupon_code: code, subtotal: String(this.subtotal()) }).toString(),
          });
          this.coupon = await res.json();
          this.couponMsg = this.coupon.valid ? '' : (this.coupon.reason || 'Cupón inválido.');
        } catch (e) {
          this.coupon = null;
          this.couponMsg = 'No se pudo validar el cupón.';
        }
      },
      confirm() {
        if (!this.items().length) return;
        if (this.belowMinimum) return;  // never open the modal below the minimum
        // The client is entered inside the modal, so it stays openable without one;
        // `canConfirm()` gates the final submit until a client is provided.
        this.modal = true;
      },
      syncCart(form) {
        const lines = Object.values(this.cart).map((item) => ({
          product_id: item.productId,
          product_variant_id: item.variantId,
          quantity: item.qty,
          modifier_option_ids: item.options,
          removed_ingredient_ids: item.removedIngredients,
        }));
        let input = form.querySelector('input[name="cart_payload"]');
        if (!input) {
          input = document.createElement('input');
          input.type = 'hidden';
          input.name = 'cart_payload';
          form.appendChild(input);
        }
        input.value = JSON.stringify(lines);
      },
      fmt,
    }));

    Alpine.data('productConfig', () => {
      const cfg = readJSON('pc-config', {});
      return {
        productId: cfg.productId || '',
        productName: cfg.productName || '',
        variants: cfg.variants || [],
        variantIngredients: cfg.variantIngredients || {},
        modifierGroups: cfg.modifierGroups || {},
        optionMeta: cfg.optionMeta || {},
        qty: 1,
        selectedVariant: '',
        selectedVariantObj: { id: '', name: '', price: 0 },
        selectedOptions: [],
        removedIngredients: [],
        notices: {},
        showErrors: false,

        init() {
          const first = this.variants.find((v) => v.available) || this.variants[0];
          if (first) {
            this.selectedVariant = first.id;
            this.selectedVariantObj = { id: first.id, name: first.name, price: first.price };
          }
        },

        isVariantSelected(id) {
          return this.selectedVariant === id;
        },
        selectVariant(id, name, price) {
          if (this.selectedVariant === id) return;
          this.selectedVariant = id;
          this.selectedVariantObj = { id, name, price };
          this.removedIngredients = [];
        },

        isSelected(id) {
          return this.selectedOptions.includes(id);
        },
        countInGroup(group) {
          return this.selectedOptions.filter((id) => group.options.includes(id)).length;
        },
        toggleOption(id, event) {
          const meta = this.optionMeta[id];
          if (!meta) return;
          const group = this.modifierGroups[meta.groupId];
          this.clearNotice(meta.groupId);

          if (this.selectedOptions.includes(id)) {
            this.selectedOptions = this.selectedOptions.filter((x) => x !== id);
            return;
          }
          if (group.max === 1) {
            this.selectedOptions = this.selectedOptions
              .filter((x) => !group.options.includes(x))
              .concat(id);
            return;
          }
          if (this.countInGroup(group) >= group.max) {
            if (event && event.target) event.target.checked = false;
            this.notices = { ...this.notices, [meta.groupId]: 'Máximo ' + group.max + ' opciones en este grupo.' };
            return;
          }
          this.selectedOptions = [...this.selectedOptions, id];
        },

        ingredientsForVariant(vId) {
          return (this.variantIngredients[vId] || []).filter((i) => i.removable);
        },
        isIngredientRemoved(id) {
          return this.removedIngredients.includes(id);
        },
        toggleIngredient(id, name, event) {
          if (event.target.checked) {
            this.removedIngredients = this.removedIngredients.filter((x) => x !== id);
          } else if (!this.removedIngredients.includes(id)) {
            this.removedIngredients = [...this.removedIngredients, id];
          }
        },

        noticeFor(groupId) {
          return this.notices[groupId] || '';
        },
        clearNotice(groupId) {
          if (!this.notices[groupId]) return;
          const next = { ...this.notices };
          delete next[groupId];
          this.notices = next;
        },
        isGroupSatisfied(groupId) {
          const g = this.modifierGroups[groupId];
          return !g || this.countInGroup(g) >= g.min;
        },
        isGroupEmpty(groupId) {
          const g = this.modifierGroups[groupId];
          return !g || this.countInGroup(g) === 0;
        },
        selectNone(groupId) {
          const g = this.modifierGroups[groupId];
          if (!g) return;
          this.selectedOptions = this.selectedOptions.filter((x) => !g.options.includes(x));
          this.clearNotice(groupId);
        },
        missingGroups() {
          return Object.keys(this.modifierGroups)
            .filter((gid) => this.modifierGroups[gid].min > 0 && !this.isGroupSatisfied(gid))
            .map((gid) => this.modifierGroups[gid]);
        },
        firstError() {
          return !this.selectedVariant || this.missingGroups().length > 0;
        },
        groupError(groupId) {
          return this.showErrors && !this.isGroupSatisfied(groupId);
        },
        groupErrorMessage(groupId) {
          const g = this.modifierGroups[groupId];
          return g.min === 1 ? 'Elegí una opción para continuar.' : 'Elegí al menos ' + g.min + ' opciones.';
        },
        errorSummary() {
          if (!this.selectedVariant) return 'Elegí una variante para continuar.';
          const missing = this.missingGroups();
          if (!missing.length) return '';
          return 'Falta completar: ' + missing.map((g) => g.name).join(', ') + '.';
        },

        totalPrice() {
          return this.selectedOptions.reduce(
            (total, id) => total + (this.optionMeta[id] ? this.optionMeta[id].priceDelta : 0),
            this.selectedVariantObj.price
          );
        },

        addToCart() {
          if (this.firstError()) {
            this.showErrors = true;
            return;
          }

          const desc = this.selectedVariantObj.name;
          const opts = this.selectedOptions
            .map((id) => this.optionMeta[id] && this.optionMeta[id].name)
            .filter(Boolean);
          const removed = this.removedIngredients
            .map((id) => (this.variantIngredients[this.selectedVariant] || []).find((i) => i.id === id))
            .map((i) => i && i.name)
            .filter(Boolean);

          const extras = [];
          if (opts.length) extras.push(opts.join(', '));
          if (removed.length) extras.push('Sin ' + removed.join(', sin '));

          const configName =
            this.productName + ' (' + desc + ')' + (extras.length ? ' - ' + extras.join(' | ') : '');

          window.dispatchEvent(
            new CustomEvent('pos-add-item', {
              detail: {
                productId: this.productId,
                variantId: this.selectedVariant,
                name: configName,
                price: this.totalPrice(),
                qty: this.qty,
                options: [...this.selectedOptions],
                removedIngredients: [...this.removedIngredients],
              },
            })
          );

          this.$el.closest('.fixed').remove();
        },

        fmt,
      };
    });
  });
})();
