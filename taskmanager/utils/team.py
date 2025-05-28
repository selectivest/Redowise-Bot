from sqlalchemy import select, and_
from ..database.models import Team, TeamMember, User, TeamMemberRole

async def get_user_managed_teams(db, user_id: int) -> list[Team]:
    """Get all teams where the user is the Owner (can manage members)"""
    print(f"DEBUG: Checking managed teams for user: {user_id}")
    query = select(Team).join(TeamMember).where(
        and_(
            TeamMember.user_id == user_id,
            TeamMember.role == TeamMemberRole.OWNER
        )
    )
    result = await db.execute(query)
    teams = result.scalars().all()
    print(f"DEBUG: Managed teams found: {teams}")
    return teams

async def get_team_members(db, team_id: int) -> list[TeamMember]:
    """Get all members of a team"""
    query = select(TeamMember).where(TeamMember.team_id == team_id)
    result = await db.execute(query)
    return result.scalars().all()

async def is_team_manager(db, user_id: int, team_id: int) -> bool:
    """Check if a user is a manager of a team"""
    query = select(TeamMember).where(
        and_(
            TeamMember.user_id == user_id,
            TeamMember.team_id == team_id,
            TeamMember.role == TeamMemberRole.MANAGER
        )
    )
    result = await db.execute(query)
    return result.first() is not None

async def get_team_member(db, user_id: int, team_id: int) -> TeamMember | None:
    """Get a specific team member"""
    query = select(TeamMember).where(
        and_(
            TeamMember.user_id == user_id,
            TeamMember.team_id == team_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() 