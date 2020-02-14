from typing import List
import tempfile
import atexit
import subprocess
import numpy as np
from CSXCAD.CSXCAD import ContinuousStructure
from pyems.port import Port
from pyems.automesh import Mesh


class Network:
    """
    A network represents an electrical network.  It consists of one or
    more ports as well as a number of components and a mesh.

    :param ports: A list of `Port` objects.
    :param mesh: The network `Mesh`.  It's generally recommended to
        leave this argument as its default value, None.  Ommitting it
        causes the mesh to be automatically generated for the network.
        Setting it will override the automatic mesh generation.
    """

    def __init__(
        self,
        csx: ContinuousStructure,
        ports: List[Port] = None,
        mesh: Mesh = None,
    ):
        """
        """
        self.csx = csx
        self.ports = ports
        self.mesh = mesh

        # set later
        self.freq = None
        self.csx_fd, self.csx_file = tempfile.mkstemp()
        # atexit.register(self._cleanup_files)

    def generate_mesh(
        self,
        lambda_min: float,
        smooth: List[float] = [1.5, 1.5, 1.5],
        expand_bounds: List[float] = [0, 0, 0, 0, 0, 0],
        simulation_bounds: List[float] = None,
    ) -> None:
        """
        Generate the mesh for the network.  This should be called
        after all ports and structures are added.
        """
        if self.mesh is None:
            self.mesh = Mesh(
                self.csx,
                lmin=lambda_min,
                mres=1 / 20,
                sres=1 / 10,
                smooth=smooth,
                min_lines=9,
                expand_bounds=expand_bounds,
                simulation_bounds=simulation_bounds,
            )
            self.mesh.generate_mesh()

        [port.snap_to_mesh(mesh=self.mesh) for port in self.ports]
        self._write_csx()

    def s_param(self, i: int, j: int) -> np.array:
        """
        Calculate the S-parameter, S_{ij}.

        :param i: First subscript of S.  Must be in the range [1,
                  num_ports]
        :param j: Second subscript of S.  Must be in the range [1,
                  num_ports]
        """
        num_ports = self._num_ports()
        if i > num_ports or j > num_ports or i < 1 or j < 1:
            raise ValueError(
                "Invalid S-parameter requested. Ensure that i and j are in "
                "the proper range for the network."
            )

        i -= 1
        j -= 1
        s = 20 * np.log10(
            self.ports[i].reflected_voltage()
            / self.ports[j].incident_voltage()
        )
        return s

    def get_mesh(self) -> Mesh:
        """
        Get the network mesh.
        """
        return self.mesh

    def calc(self, sim_dir, freq) -> None:
        """
        Calculate all port parameters.
        """
        self.freq = freq
        [port.calc(sim_dir=sim_dir, freq=freq) for port in self.ports]

    def add_port(self, port: Port) -> None:
        """
        Add a `Port` to the network.
        """
        self.ports.append(port)

    def get_ports(self) -> List[Port]:
        """
        Retrieve all network ports.
        """
        return self.ports

    def _num_ports(self) -> int:
        """
        Return the number of ports in the network.
        """
        return len(self.ports)

    def save(self, file_path: str) -> None:
        """
        Save the XML CSXCAD structure to a file.

        :param file_path: The file path where the XML file should be
            saved.
        """
        self.csx.Write2XML(file_path)

    def _write_csx(self) -> None:
        """
        Write CSX data to a temporary file.
        """
        self.csx.Write2XML(self.csx_file)

    def view(self) -> None:
        """
        View the CSX network.
        """
        subprocess.run(["AppCSXCAD", self.csx_file])

    # def _cleanup_files(self) -> None:
    #     """
    #     """
    #     self.csx_fd.close()
