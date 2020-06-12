import browserHistory from "../../utils/browserHistory";
import React from "react";
import {
  Alignment,
  Button,
  Classes,
  Navbar,
  NavbarDivider,
  NavbarGroup,
  NavbarHeading,
} from "@blueprintjs/core";
const Users: React.FC = () => {
  let alignRight = false;
  return (
    <Navbar>
      <NavbarGroup align={alignRight ? Alignment.RIGHT : Alignment.LEFT}>
        <NavbarHeading
          onClick={() => {
            browserHistory.push("/");
          }}
        >
          Smartsleep Admin
        </NavbarHeading>
        <NavbarDivider />
        <Button
          className={Classes.MINIMAL}
          icon="user"
          text="Users"
          onClick={() => {
            browserHistory.push("/users");
          }}
        />
        {/* <Button className={Classes.MINIMAL} icon="document" text="Files" /> */}
      </NavbarGroup>
    </Navbar>
  );
};
export default Users;
