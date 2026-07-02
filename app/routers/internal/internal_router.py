from fastapi import APIRouter, HTTPException
from app.database.models.user import User

router = APIRouter(prefix="/internal", tags=["Internal APIs"])


@router.get("/users/{user_id}/org-tree")
async def get_user_org_tree(user_id: int):
    """
    Retorna o caminho ascendente (ancestors) desde a OrgUnit do User
    até à raiz da empresa, além das apps a que tem acesso.
    Usado internamente por outros microsserviços.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tree = []
    from app.database.repository.auth.auth_repository import AuthRepository
    primary_company = await AuthRepository.get_user_primary_company(user)
    
    if primary_company and primary_company.org_unit_id:
        from app.database.repository.org_unit.org_unit_repository import OrgUnitRepository
        rows = await OrgUnitRepository.get_ancestors(primary_company.org_unit_id)
        tree = rows

    return {"user_id": user.id, "org_unit_ancestors": tree}
