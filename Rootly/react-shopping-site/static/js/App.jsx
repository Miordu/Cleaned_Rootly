function App() {
  const [melons, setMelons] = React.useState({});
  const [shoppingCart, setShoppingCart] = React.useState({});
  
  // Add this useEffect hook to fetch melons when component mounts
  React.useEffect(() => {
    fetch('/api/melons')
      .then((response) => response.json())
      .then((melonData) => {
        setMelons(melonData);
      });
  }, []); // Empty dependency array means this effect runs once on mount
  
  function addMelonToCart(melonCode) {
    setShoppingCart((currentShoppingCart) => {
      // Create a copy of the current shopping cart
      const newShoppingCart = Object.assign({}, currentShoppingCart);
      
      // If the melon is already in the cart, increment its quantity
      if (newShoppingCart[melonCode]) {
        newShoppingCart[melonCode] += 1;
      } else {
        // Otherwise, add it to the cart with quantity 1
        newShoppingCart[melonCode] = 1;
      }
      
      return newShoppingCart;
    });
  }
  
  return (
    <ReactRouterDOM.BrowserRouter>
      <Navbar logo="/static/img/watermelon.png" brand="Ubermelon" />
      <div className="container-fluid">
        <ReactRouterDOM.Route exact path="/">
          <Homepage />
        </ReactRouterDOM.Route>
        <ReactRouterDOM.Route exact path="/shop">
          <AllMelonsPage melons={melons} handleAddToCart={addMelonToCart} />
        </ReactRouterDOM.Route>
        <ReactRouterDOM.Route exact path="/cart">
          <ShoppingCartPage cart={shoppingCart} melons={melons} />
        </ReactRouterDOM.Route>
      </div>
    </ReactRouterDOM.BrowserRouter>
  );
}

ReactDOM.render(<App />, document.querySelector('#root'));