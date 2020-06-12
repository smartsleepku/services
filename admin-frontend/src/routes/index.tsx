import React from "react";
import { Switch, Route } from "react-router-dom";
import Users from "../pages/Users";
import Landing from "../pages/Landing";

const Routes: React.FC = () => (
  <Switch>
    <Route exact path="/" component={Landing} />
    <Route exact path="/users" component={Users} />
  </Switch>
);
export default Routes;
