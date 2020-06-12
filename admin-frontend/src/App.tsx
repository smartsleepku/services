import React from "react";
import { Router } from "react-router-dom";
import Routes from "./routes";
import browserHistory from "./utils/browserHistory";
import Layout from "./components/Layout";
import "./App.css";

function App() {
  return (
    <Router history={browserHistory}>
      <Layout>
        <Routes />
      </Layout>
    </Router>
  );
}

export default App;
