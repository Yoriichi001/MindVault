/* ======================================================
   OAK & GRAIN
   Furniture Catalogue Interaction
====================================================== */


/* ======================================================
   1. PRODUCT DATA
====================================================== */

const products = [

    {
        id: 1,
        name: "Structure & Interpretation of Computer Programs",
        category: "Books",
        author: "Harold Abelson & Gerald Jay Sussman",
        material: "Computer Science",
        finish: "Hardcover Codex",
        pages: 657,
        image: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=1000&q=85",
        description: "A foundational masterpiece of computer science education. It explores computational abstractions, recursive procedures, higher-order functions, and metacircular evaluators.",
        shortDescription: "Building abstractions with procedures and data structures."
    },

    {
        id: 2,
        name: "Principles of Quantum Mechanics",
        category: "Books",
        author: "Paul A. M. Dirac",
        material: "Theoretical Physics",
        finish: "Oxford Archive",
        pages: 314,
        image: "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=1000&q=85",
        description: "The definitive treatise on quantum theory by one of its principal founders. Formulates the transformation theory, bra-ket notation, and relativistic wave mechanics.",
        shortDescription: "Foundational treatise on quantum state vectors and superposition."
    },

    {
        id: 3,
        name: "Attention Is All You Need",
        category: "Research Papers",
        author: "Ashish Vaswani, Noam Shazeer et al.",
        material: "Deep Learning & NLP",
        finish: "NeurIPS Publication",
        pages: 15,
        image: "https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=1000&q=85",
        description: "The seminal paper proposing the Transformer architecture, dispensing entirely with recurrence and convolutions in favor of self-attention mechanisms.",
        shortDescription: "The seminal Transformer architecture underpinning modern AI."
    },

    {
        id: 4,
        name: "A Mathematical Theory of Communication",
        category: "Research Papers",
        author: "Claude E. Shannon",
        material: "Information Theory",
        finish: "Bell Labs Archive",
        pages: 55,
        image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=85",
        description: "The 1948 foundational work that created modern information theory, defining entropy, bits, channel capacity, and source coding theorems.",
        shortDescription: "The genesis of digital communication and entropy."
    },

    {
        id: 5,
        name: "Data Structures & Algorithms: Complete Synthesis",
        category: "Study Materials",
        author: "MindVault Academic Editorial Board",
        material: "Algorithms & Analysis",
        finish: "Scholar Compendium",
        pages: 42,
        image: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1000&q=85",
        description: "Comprehensive synthesis covering asymptotic analysis, balanced search trees, graph theory, shortest path algorithms, and dynamic programming paradigms.",
        shortDescription: "Essential revision notes and algorithmic blueprints for engineers."
    },

    {
        id: 6,
        name: "Linear Algebra & Matrix Decompositions for ML",
        category: "Study Materials",
        author: "Dr. Elena Rostova",
        material: "Applied Mathematics",
        finish: "Atelier Study Guide",
        pages: 28,
        image: "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=1000&q=85",
        description: "Rigorous study guide and summary sheets for vector spaces, projections, eigenvalue decomposition, Principal Component Analysis (PCA), and SVD.",
        shortDescription: "Geometric insights into high-dimensional matrix transformations."
    }

];


/* ======================================================
   2. DOM REFERENCES
====================================================== */

const screens = {
    cover: document.getElementById("coverScreen"),
    login: document.getElementById("loginScreen"),
    shop: document.getElementById("shopScreen"),
    detail: document.getElementById("detailScreen")
};

const mainBook = document.getElementById("mainBook");

const openBookBtn = document.getElementById("openBookBtn");

const loginForm = document.getElementById("loginForm");

const productGrid = document.getElementById("productGrid");

const detailBook = document.getElementById("detailBook");

const turningPage = document.getElementById("turningPage");

const cartCount = document.getElementById("cartCount");

const cartModal = document.getElementById("cartModal");

const toast = document.getElementById("toast");


/* ======================================================
   3. SCREEN NAVIGATION
====================================================== */

let currentScreen = "cover";

function showScreen(name) {

    if (!screens[name]) {
        return;
    }

    Object.values(screens).forEach(screen => {
        screen.classList.remove("active");
    });

    screens[name].classList.add("active");

    currentScreen = name;

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* ======================================================
   4. TOAST MESSAGE
====================================================== */

let toastTimer;

function showToast(message) {

    toast.textContent = message;

    toast.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2600);

}


/* ======================================================
   5. OPEN THE ANTIQUE BOOK
====================================================== */

let openingBook = false;

openBookBtn.addEventListener("click", () => {

    if (openingBook) {
        return;
    }

    openingBook = true;

    mainBook.classList.add("opening");

    openBookBtn.disabled = true;

    setTimeout(() => {

        showScreen("login");

        mainBook.classList.remove("opening");

        openBookBtn.disabled = false;

        openingBook = false;

    }, 1500);

});


/* ======================================================
   6. RETURN TO COVER
====================================================== */

document.getElementById("backToCover")
    .addEventListener("click", () => {

        showScreen("cover");

    });


document.getElementById("homeBtn")
    .addEventListener("click", event => {

        event.preventDefault();

        showScreen("cover");

    });


/* ======================================================
   7. LOGIN DEMONSTRATION
====================================================== */

loginForm.addEventListener("submit", event => {

    event.preventDefault();

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    if (!email || !password) {

        showToast("Please complete both fields.");

        return;

    }

    const submitButton =
        loginForm.querySelector("button");

    submitButton.disabled = true;

    submitButton.innerHTML =
        "OPENING THE COLLECTION...";

    setTimeout(() => {

        renderProducts("all");

        showScreen("shop");

        submitButton.disabled = false;

        submitButton.innerHTML =
            'ENTER THE COLLECTION <span>→</span>';

    }, 650);

});


/* ======================================================
   8. PRICE FORMATTING
====================================================== */

function formatPrice(price) {

    return new Intl.NumberFormat("en-IN", {

        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0

    }).format(price);

}


/* ======================================================
   9. RENDER PRODUCT CATALOGUE
====================================================== */

function renderProducts(category = "all") {

    productGrid.innerHTML = "";

    const filteredProducts = products.filter(product => {

        return category === "all" ||
               product.category === category;

    });

    filteredProducts.forEach((product, index) => {

        const card = document.createElement("article");

        card.className = "product-card";
        card.tabIndex = 0;
        card.setAttribute("role", "button");
        card.setAttribute("aria-label", `Open details for ${product.name}`);

        card.style.animationDelay =
            `${index * 100}ms`;

        card.innerHTML = `

            <div class="product-card-inner">

                <div class="product-image-wrap">

                    <img
                        class="product-image"
                        src="${product.image}"
                        alt="${product.name}"
                        loading="lazy"
                    >

                    <div class="image-overlay"></div>

                </div>

                <div class="product-info">

                    <p class="product-category">
                        ${product.category}
                    </p>

                    <h3>
                        ${product.name}
                    </h3>

                    <p class="product-description">
                        ${product.shortDescription}
                    </p>

                    <div class="product-bottom">

                        <span class="product-price">
                            ${formatPrice(product.price)}
                        </span>

                        <span class="view-product">
                            OPEN THE PAGE ↗
                        </span>

                    </div>

                </div>

            </div>

        `;

        card.addEventListener("click", () => {

            openProductDetails(product.id);

        });

        card.addEventListener("keydown", event => {

            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openProductDetails(product.id);
            }

        });

        productGrid.appendChild(card);

    });

}


/* ======================================================
   10. FILTER PRODUCTS
====================================================== */

const filterButtons =
    document.querySelectorAll(".filter-button");

filterButtons.forEach(button => {

    button.addEventListener("click", () => {

        filterButtons.forEach(item => {
            item.classList.remove("active");
        });

        button.classList.add("active");
        filterButtons.forEach(item => {
            item.setAttribute("aria-pressed", String(item === button));
        });

        renderProducts(button.dataset.category);

    });

});


/* ======================================================
   11. PRODUCT DETAIL CONTENT
====================================================== */

let selectedProduct = null;

function populateProductDetails(product) {

    document.getElementById("detailName").textContent =
        product.name;

    document.getElementById("detailNameLeft").textContent =
        product.name;

    document.getElementById("detailPrice").textContent =
        `${product.pages} Pages · Open Academic Access`;

    document.getElementById("detailImage").src =
        product.image;

    document.getElementById("detailImage").alt =
        product.name;

    document.getElementById("detailDescription").textContent =
        product.shortDescription;

    document.getElementById("detailDescriptionLeft").textContent =
        product.description;

    document.getElementById("detailMaterial").textContent =
        product.material;

    document.getElementById("detailFinish").textContent =
        product.finish;

    document.getElementById("detailCategory").textContent =
        product.category.toUpperCase();

}


/* ======================================================
   12. OPEN PRODUCT WITH PAGE-TURN ANIMATION
====================================================== */

let pageTurning = false;

function openProductDetails(productId) {

    const product = products.find(item => {
        return item.id === productId;
    });

    if (!product || pageTurning) {
        return;
    }

    selectedProduct = product;

    populateProductDetails(product);

    const previousScreen = currentScreen;

    if (previousScreen === "detail") {

        detailBook.classList.remove("turning");

        void detailBook.offsetWidth;

        pageTurning = true;

        detailBook.classList.add("turning");

        setTimeout(() => {

            detailBook.classList.remove("turning");

            showScreen("detail");

            pageTurning = false;

        }, 1150);

        return;
    }

    detailBook.classList.remove("turning");

    void detailBook.offsetWidth;

    pageTurning = true;
    detailBook.classList.add("turning");
    showScreen("detail");

    setTimeout(() => {
        detailBook.classList.remove("turning");
        pageTurning = false;
    }, 1150);

}


/* ======================================================
   13. RETURN TO CATALOGUE
====================================================== */

document.getElementById("backToShop")
    .addEventListener("click", () => {

        showScreen("shop");

    });


/* ======================================================
   14. CART
====================================================== */

let cart = [];

function addToCart(product) {

    cart.push(product);

    cartCount.textContent = cart.length;

    showToast(`${product.name} added to your bag.`);

}


/* Add product */

document.getElementById("addToCartBtn")
    .addEventListener("click", () => {

        if (!selectedProduct) {
            return;
        }

        addToCart(selectedProduct);

    });


/* ======================================================
   15. CART MODAL
====================================================== */

document.getElementById("cartButton")
    .addEventListener("click", openCart);


function openCart() {

    renderCart();

    cartModal.classList.add("open");

}


function closeCart() {

    cartModal.classList.remove("open");

}


document.getElementById("closeCart")
    .addEventListener("click", closeCart);


cartModal.addEventListener("click", event => {

    if (event.target === cartModal) {

        closeCart();

    }

});


function renderCart() {

    const cartItems =
        document.getElementById("cartItems");

    const cartTotal =
        document.getElementById("cartTotal");

    cartItems.innerHTML = "";

    if (cart.length === 0) {

        cartItems.innerHTML = `
            <p style="
                margin-top: 25px;
                font-family: Georgia, serif;
                font-style: italic;
                color: #80664a;
            ">
                Your collection bag is empty.
            </p>
        `;

        cartTotal.textContent = formatPrice(0);

        return;

    }

    cart.forEach((product, index) => {

        const item = document.createElement("div");

        item.className = "cart-item";

        item.innerHTML = `

            <div>

                <p class="cart-item-name">
                    ${product.name}
                </p>

                <p style="
                    margin-top: 5px;
                    color: #856a49;
                    font-size: 10px;
                ">
                    ${product.material}
                </p>

            </div>

            <span class="cart-item-price">
                ${formatPrice(product.price)}
            </span>

        `;

        cartItems.appendChild(item);

    });

    const total = cart.reduce((sum, product) => {

        return sum + product.price;

    }, 0);

    cartTotal.textContent = formatPrice(total);

}


/* ======================================================
   16. INITIALIZE
====================================================== */

renderProducts("all");