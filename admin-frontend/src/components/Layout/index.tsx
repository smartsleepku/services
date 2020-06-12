import React from "react";
import Header from "../Header";
function Layout(props: React.PropsWithChildren<{}>) {
  return (
    <div>
      <Header />
      <div className="content">{props.children}</div>
    </div>
  );
}

export default Layout;
