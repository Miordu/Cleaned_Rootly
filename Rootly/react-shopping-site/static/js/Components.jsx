function Homepage(props) {
  return (
    <div id="home-banner" className="row">
      <div className="col">
        <h1>Ubermelon</h1>
        <p className="lead">Melons on demand.</p>
      </div>
    </div>
  );
}

function AllMelonsPage(props) {
  const { melons, handleAddToCart } = props;
  const melonCards = [];
  
  for (const [melonCode, melon] of Object.entries(melons)) {
    const melonCard = (
      <MelonCard
        key={melonCode}
        code={melonCode}
        name={melon.name}
        imgUrl={melon.image_url}
        price={melon.price}
        handleAddToCart={handleAddToCart}
      />
    );
    melonCards.push(melonCard);
  }
  
  return (
    <React.Fragment>
      <h1>All Melons</h1>
      <div id="shopping">
        <div className="col-12 col-md-9 d-flex flex-wrap">{melonCards}</div>
      </div>
    </React.Fragment>
  );
}

function ShoppingCartPage(props) {
  const { cart, melons } = props;
  
  // Calculate the cart total and create cart items for the table
  let total = 0;
  const cartRows = [];
  
  for (const [melonCode, quantity] of Object.entries(cart)) {
    const melon = melons[melonCode];
    
    // Skip if the melon doesn't exist in our melons data
    if (!melon) continue;
    
    // Calculate the cost for this melon
    const subtotal = melon.price * quantity;
    total += subtotal;
    
    cartRows.push(
      <tr key={melonCode}>
        <td>{melon.name}</td>
        <td>{quantity}</td>
        <td>${subtotal.toFixed(2)}</td>
      </tr>
    );
  }
  
  return (
    <React.Fragment>
      <h1>Shopping Cart</h1>
      <div className="col-6">
        <table className="table">
          <thead>
            <tr>
              <th>Melon</th>
              <th>Quantity</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {cartRows}
          </tbody>
        </table>
        <p className="lead">Total: ${total.toFixed(2)}</p>
      </div>
    </React.Fragment>
  );
}

function Navbar(props) {
  const { logo, brand } = props;
  return (
    <nav>
      <ReactRouterDOM.Link to="/" className="havbar-brand d-flex justify-content-center">
        <img src={logo} height="30" alt="logo" />
        <span>{brand}</span>
      </ReactRouterDOM.Link>
      <section className="d-flex justify-content-center">
        <ReactRouterDOM.NavLink
          to="/shop"
          activeClassName="navlink-active"
          className="nav-link nav-item"
        >
          Shop for Melons
        </ReactRouterDOM.NavLink>
        <ReactRouterDOM.NavLink
          to="/cart"
          activeClassName="navlink-active"
          className="nav-link nav-item"
        >
          Shopping Cart
        </ReactRouterDOM.NavLink>
      </section>
    </nav>
  );
}

function MelonCard(props) {
  const { code, name, imgUrl, price, handleAddToCart } = props;
  return (
    <div className="card melon-card">
      <ReactRouterDOM.Link to={`/shop/${code}`}>
        <img src={imgUrl} className="card-img-top" alt="" />
      </ReactRouterDOM.Link>
      <div className="card-body">
        <h5 className="card-title">
          <ReactRouterDOM.Link to={`/shop/${code}`}>{name}</ReactRouterDOM.Link>
        </h5>
      </div>
      <div className="card-body pt-0 container-fluid">
        <div className="row">
          <div className="col-12 col-lg-6">
            <span className="lead price d-inline-block">${price.toFixed(2)}</span>
          </div>
          <div className="col-12 col-lg-6">
            <button
              type="button"
              className="btn btn-sm btn-success d-inline-block"
              onClick={() => handleAddToCart && handleAddToCart(code)}
            >
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}