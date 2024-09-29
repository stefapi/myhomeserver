from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/register")


@controller(router)
class RegistrationController(BasePublicController):
    event_bus: EventBusService = Depends(EventBusService.as_dependency)

    @router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
    def register_new_user(self, data: CreateUserRegistration):
        settings = get_app_settings()

        if not settings.ALLOW_SIGNUP and data.group_token is None or data.group_token == "":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse.respond("User Registration is Disabled"),
            )

        registration_service = RegistrationService(
            self.logger,
            get_repositories(self.session, group_id=None, household_id=None),
            self.translator,
        )

        result = registration_service.register_user(data)

        self.event_bus.dispatch(
            integration_id="registration",
            group_id=result.group_id,
            household_id=result.household_id,
            event_type=EventTypes.user_signup,
            document_data=EventUserSignupData(username=result.username, email=result.email),
        )

        return result
