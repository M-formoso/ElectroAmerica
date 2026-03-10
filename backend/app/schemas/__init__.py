from app.schemas.usuario import (
    UsuarioBase, UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    Token, TokenPayload, LoginRequest
)
from app.schemas.proyecto import (
    ProyectoBase, ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoDetailResponse
)
from app.schemas.etapa import (
    EtapaBase, EtapaCreate, EtapaUpdate, EtapaResponse
)
from app.schemas.item_trabajo import (
    ItemTrabajoBase, ItemTrabajoCreate, ItemTrabajoUpdate, ItemTrabajoResponse
)
from app.schemas.material import (
    MaterialBase, MaterialCreate, MaterialUpdate, MaterialResponse,
    AsignacionMaterialCreate, AsignacionMaterialResponse,
    IngresoStockCreate, MovimientoStockResponse
)
from app.schemas.equipo import (
    EquipoBase, EquipoCreate, EquipoUpdate, EquipoResponse,
    AsignacionEquipoCreate, AsignacionEquipoResponse
)
from app.schemas.gasto import (
    GastoBase, GastoCreate, GastoUpdate, GastoResponse,
    CategoriaGastoCreate, CategoriaGastoResponse
)
from app.schemas.foto import (
    FotoCreate, FotoUpdate, FotoResponse
)
from app.schemas.finanzas import (
    PrecioItemCreate, PrecioItemResponse,
    ResumenFinancieroProyecto, ResumenFinancieroGeneral
)
from app.schemas.reporte import (
    ReporteCreate, ReporteResponse
)
