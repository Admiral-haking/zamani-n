/* نگاشت محصولات فهرست ثابت سایت به محصولات واقعی سرور
 *
 * نام محصولات داخل کد سایت با نام‌های دیتابیس یکی نیست:
 *   فرانت : «همبرگر ۱۰۰ گرمی ۹۰٪»  ←  دیتابیس: «همبرگر ۹۰٪ ۱۰۰ گرم»
 * برای همبرگرها «تطابق دقیق نام» شکست می‌خورد، پس یک تطبیق جایگزین با
 * امضا (امضای ارقامِ داخل نام) هم انجام می‌شود که فقط وقتی یکتا باشد
 * پذیرفته می‌شود. استیک/رست‌بیف نامشان دقیقاً یکی است و همان مسیر اول کافی است.
 *
 * کاربرد: شناسه محصول سرور (catalogId) و تعداد بسته در هر کارتن (pack_per_carton)
 * برای هر آیتم سبد خرید.
 */
(function (root) {
    'use strict';

    // کلید قیمت هر محصول سایت (همان کلیدهای price_list ثبت‌شده در منشی/پخش‌کننده)
    var FRONT_PRICE_KEYS = {
        1: 'همبرگر ۱۰۰ گرمی ۹۰٪',
        2: 'همبرگر ۱۲۵ گرمی ۹۰٪',
        3: 'همبرگر ۱۵۰ گرمی ۹۰٪',
        4: 'همبرگر ۱۸۰ گرمی ۹۰٪',
        5: 'همبرگر ۱۰۰ گرمی ۶۰٪',
        6: 'همبرگر ۱۲۵ گرمی ۶۰٪',
        101: 'استیک ۹۰٪',
        102: 'استیک ۶۰٪',
        103: 'استیک ویژه',
        104: 'رست بیف کیلویی'
    };

    var FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
    var AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';

    function toEN(value) {
        var s = String(value == null ? '' : value);
        var out = '';
        for (var i = 0; i < s.length; i++) {
            var ch = s.charAt(i);
            var fa = FA_DIGITS.indexOf(ch);
            if (fa > -1) { out += String(fa); continue; }
            var ar = AR_DIGITS.indexOf(ch);
            if (ar > -1) { out += String(ar); continue; }
            out += ch;
        }
        return out;
    }

    function normalizeName(value) {
        return toEN(value).replace(/[٪%ـ\s\-_.،,]/g, '').toLowerCase();
    }

    // امضای ارقام داخل نام (مرتب‌شده) تا «همبرگر ۱۰۰ گرمی ۹۰٪» با
    // «همبرگر ۹۰٪ ۱۰۰ گرم» یکی دیده شود
    function digitSignature(value) {
        var m = toEN(value).match(/\d+/g);
        if (!m) return '';
        return m.slice().sort().join('|');
    }

    var index = null;

    function emptyIndex() {
        return {
            byName: {},        // نام نرمال‌شده محصول سرور → شناسه سرور
            byFrontKey: {},    // کلید قیمت فرانت → شناسه سرور
            byFrontId: {},     // شناسه محصول داخل سایت → شناسه سرور
            packByFrontKey: {},// کلید قیمت فرانت → تعداد بسته در کارتن
            packByFrontId: {}  // شناسه محصول داخل سایت → تعداد بسته در کارتن
        };
    }

    function toArray(payload) {
        if (Array.isArray(payload)) return payload;
        if (payload && Array.isArray(payload.results)) return payload.results;
        if (payload && Array.isArray(payload.items)) return payload.items;
        return [];
    }

    function build(payload) {
        var products = toArray(payload);
        var next = emptyIndex();
        var bySignature = {};

        products.forEach(function (p) {
            if (!p || p.id == null) return;
            var name = normalizeName(p.name);
            var pack = parseInt(p.pack_per_carton != null ? p.pack_per_carton : p.carton_size, 10);
            if (!pack || pack < 1) pack = 1;

            next.byName[name] = p.id;
            next.byFrontKey[name] = p.id;
            next.packByFrontKey[name] = pack;

            var sig = digitSignature(p.name);
            if (sig) {
                if (!bySignature[sig]) bySignature[sig] = [];
                bySignature[sig].push({ id: p.id, pack: pack });
            }
        });

        Object.keys(FRONT_PRICE_KEYS).forEach(function (frontId) {
            var key = normalizeName(FRONT_PRICE_KEYS[frontId]);
            var hit = null;

            if (next.byName[key] != null) {
                hit = { id: next.byName[key], pack: next.packByFrontKey[key] || 1 };
            } else {
                var sig = digitSignature(key);
                var list = sig ? (bySignature[sig] || []) : [];
                // فقط وقتی دقیقاً یک محصول این امضا را دارد می‌پذیریم
                if (list.length === 1) hit = list[0];
            }

            if (hit) {
                next.byFrontId[frontId] = hit.id;
                next.packByFrontId[frontId] = hit.pack;
                next.byFrontKey[key] = hit.id;
                next.packByFrontKey[key] = hit.pack;
            }
        });

        index = next;
        return index;
    }

    function ready() {
        return !!index;
    }

    function reset() {
        index = null;
    }

    // شناسه محصول سرور برای یک آیتم سبد خرید
    function catalogIdFor(item) {
        if (!item) return null;

        // ۱) قبلاً روی آیتم ثبت شده است
        if (item.catalogId != null && item.catalogId !== '') return Number(item.catalogId);

        if (index) {
            // ۲) شناسه داخل سایت (فهرست ثابت محصولات)
            if (item.frontId != null && index.byFrontId[item.frontId] != null) {
                return index.byFrontId[item.frontId];
            }
            if (item.id != null && index.byFrontId[item.id] != null) {
                return index.byFrontId[item.id];
            }
            // ۳) نام محصول یا کلید قیمت (نام سروری هم همین‌جا پیدا می‌شود)
            var key = normalizeName(item.priceKey || item.name || '');
            if (key && index.byFrontKey[key] != null) return index.byFrontKey[key];
        }

        // ۴) شناسه‌ای که خود آیتم از سرور گرفته است
        if (item.product != null && item.product !== '') return Number(item.product);

        return null;
    }

    // تعداد بسته در هر کارتن برای یک آیتم سبد خرید
    function packFor(item) {
        if (!item) return 1;
        if (item.packPerCarton != null) {
            var explicit = parseInt(item.packPerCarton, 10);
            if (explicit && explicit > 0) return explicit;
        }
        if (index) {
            if (item.frontId != null && index.packByFrontId[item.frontId]) return index.packByFrontId[item.frontId];
            if (item.id != null && index.packByFrontId[item.id]) return index.packByFrontId[item.id];
            var byKey = index.packByFrontKey[normalizeName(item.priceKey || '')];
            if (byKey) return byKey;
            var byName = index.packByFrontKey[normalizeName(item.name || '')];
            if (byName) return byName;
        }
        return 1;
    }

    // شناسه سرور یک محصولِ فهرست ثابت سایت
    function catalogIdForFrontId(frontId) {
        if (index && index.byFrontId[frontId] != null) return index.byFrontId[frontId];
        return null;
    }

    function packForFrontId(frontId) {
        if (index && index.packByFrontId[frontId]) return index.packByFrontId[frontId];
        return 1;
    }

    function frontPriceKey(frontId) {
        return FRONT_PRICE_KEYS[frontId] || null;
    }

    root.ZamaniProductMap = {
        FRONT_PRICE_KEYS: FRONT_PRICE_KEYS,
        build: build,
        ready: ready,
        reset: reset,
        normalizeName: normalizeName,
        toEN: toEN,
        digitSignature: digitSignature,
        catalogIdFor: catalogIdFor,
        packFor: packFor,
        catalogIdForFrontId: catalogIdForFrontId,
        packForFrontId: packForFrontId,
        frontPriceKey: frontPriceKey
    };
})(window);
