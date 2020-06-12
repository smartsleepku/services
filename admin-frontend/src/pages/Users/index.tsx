import React, { useState, useEffect } from "react";
import CreateUsers from "../../components/CreateUsers";
import DeleteUsers from "../../components/DeleteUsers";
const Users: React.FC = () => {
  return (
    <>
      <CreateUsers />
      <DeleteUsers />
    </>
  );
};

export default Users;
