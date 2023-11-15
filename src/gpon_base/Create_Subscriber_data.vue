<template>
  <div id="app">
    <div class="header">
      <img class="header-image" src="/static/img/gpon/subscriber-data.svg" alt="create-tech-data-image">
      <h2>Добавление абонентского подключения</h2>
    </div>

    <div class="plate shadow py-4 w-75 container">

      <StepMenu
          class="p-2"
          :current-step="current_step"
          :is-mobile="isMobile"
          :steps-text="['Тех. данные', 'Абон. данные', 'Подключение']">
      </StepMenu>

      <!-- FIRST STEP -->
      <div v-if="current_step===1" class="p-4">

        <!-- ВЫБИРАЕМ -->
        <div class="d-flex align-items-center flex-wrap">
          <div class="py-2 w-100">
            <h6 class="px-2">OLT оборудование
              <Asterisk/>
            </h6>
            <Dropdown v-model="formData.techData.deviceName" :options="devicesList" filter
                      :option-label="x => x"
                      :class="formState.firstStep.deviceName.valid?['flex-wrap', 'w-100']:['flex-wrap', 'w-100', 'p-invalid']"
                      @change="deviceHasChanged" placeholder="Выберите устройство">
              <template #value="slotProps">
                <div v-if="slotProps.value">{{ slotProps.value }}</div>
                <span v-else>{{ slotProps.placeholder }}</span>
              </template>
              <template #option="slotProps">{{ slotProps.option }}</template>
            </Dropdown>
          </div>

          <!-- ПОИСК ПОРТОВ У ВЫБРАННОГО ОБОРУДОВАНИЯ -->
          <div v-if="formData.techData.deviceName" class="w-100">
            <h6 class="px-2">Порт
              <Asterisk/>
            </h6>
            <Dropdown v-model="formData.techData.devicePort" :options="devicePortList" filter
                      :class="formState.firstStep.devicePort.valid?['w-100']:['p-invalid', 'w-100']"
                      :option-label="x => x"
                      @change="portHasChanged"
                      optionLabel="name" placeholder="Выберите порт">
              <template #value="slotProps">
                <div v-if="slotProps.value">{{ slotProps.value }}</div>
                <span v-else>{{ slotProps.placeholder }}</span>
              </template>
              <template #option="slotProps">
                <div>{{ slotProps.option }}</div>
              </template>
            </Dropdown>
          </div>
        </div>

        <br>

        <div v-if="formData.techData.devicePort" class="w-100">
          <!-- ПОИСК ВСЕХ ДОМОВ ДЛЯ ВЫБРАННОГО OLT ПОРТА -->
          <AddressGetCreate @change="addressHasChanged" :is-mobile="isMobile" :allow-create="false"
                            :valid="formState.firstStep.address.valid"
                            :data="formData.techData"
                            :get-from-device-port="{
                              deviceName: formData.techData.deviceName,
                              devicePort: formData.techData.devicePort
                            }">
          </AddressGetCreate>
        </div>

        <br>

        <div v-if="formData.techData.address">
          <!-- ПОИСК СПЛИТТЕРОВ/РАЙЗЕРОВ В ВЫБРАННОМ ДОМЕ -->
          <SplittersRizersFind @change="(e) => {formData.techData.end3 = e.value; end3HasChanged()}"
                               :valid="formState.firstStep.end3.valid"
                               :init="formData.techData.end3"
                               :fromAddressID="formData.techData.address.id">
          </SplittersRizersFind>
        </div>

        <br>

        <div v-if="formData.techData.end3 && formData.techData.address">
          <!-- ПОИСК СВОБОДНОГО ПОДКЛЮЧЕНИЯ У ВЫБРАННОГО СПЛИТТЕРА/РАЙЗЕРА -->
          <SelectSplitterRizerPort :init="formData.techData.end3Port"
                                   :valid="formState.firstStep.end3Port.valid"
                                   :end3ID="formData.techData.end3.id"
                                   @change="(e) => {formData.techData.end3Port = e.value; formState.firstStep.end3Port.valid = true}"
                                   :get-from="formData.techData.end3" :type="formData.techData.end3.type"
                                   :only-unused-ports="true">
          </SelectSplitterRizerPort>
        </div>

      </div>

      <!-- SECOND STEP -->
      <div v-else-if="current_step===2" class="p-4">

        <CustomerSearch @select="selectedSubscriber" :is-mobile="isMobile"/>

        <Button v-if="formState.secondStep.selected" size="small" @click="unselectSubscriber">Указать вручную</Button>

        <div class="p-2">
          <Dropdown v-if="!formState.secondStep.selected"
                    v-model="formData.customer.type"
                    :options="['person','company','contract']" style="width: 100%"
                    placeholder="Выберите тип абонента" class="w-full md:w-14rem">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex align-items-center"
                   v-html="subscriberVerbose(slotProps.value)"></div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex align-items-center" v-html="subscriberVerbose(slotProps.option)"></div>
            </template>
          </Dropdown>
          <div v-else>
            <div class="p-3 border rounded" v-html="subscriberVerbose(formData.customer.type)"></div>
          </div>
        </div>

        <div v-if="formData.customer.type==='person'" class="d-flex flex-wrap py-2">
          <div class="input-part">
            <h6 class="px-2">Фамилия
              <Asterisk/>
            </h6>
            <InputText v-if="!formState.secondStep.selected"
                       v-model.trim="formData.customer.surname" type="text" style="width: 100%"
                       :class="!formState.secondStep.person.surname.valid?['p-invalid']:[]"/>
            <div v-else class="p-3 border rounded-2">{{ formData.customer.surname }}</div>
            <InlineMessage v-if="customerFirstNameError" severity="error">{{ customerFirstNameError }}</InlineMessage>
          </div>

          <div class="input-part">
            <h6 class="px-2">Имя
              <Asterisk/>
            </h6>
            <InputText v-if="!formState.secondStep.selected"
                       v-model.trim="formData.customer.firstName" type="text" style="width: 100%"
                       :class="!formState.secondStep.person.firstName.valid?['p-invalid']:[]"/>
            <div v-else class="p-3 border rounded-2">{{ formData.customer.firstName }}</div>
            <InlineMessage v-if="customerSurnameError" severity="error">{{ customerSurnameError }}</InlineMessage>
          </div>

          <div class="input-part">
            <h6 class="px-2">Отчество
              <Asterisk/>
            </h6>
            <InputText v-if="!formState.secondStep.selected"
                       v-model.trim="formData.customer.lastName" type="text" style="width: 100%"
                       :class="!formState.secondStep.person.lastName.valid?['p-invalid']:[]"/>
            <div v-else class="p-3 border rounded-2">{{ formData.customer.lastName }}</div>
            <InlineMessage v-if="customerLastNameError" severity="error">{{ customerLastNameError }}</InlineMessage>
          </div>
        </div>

        <div v-else class="d-flex py-2">
          <div class="p-2 w-100">
            <h6 class="px-2">Название кампании
              <Asterisk/>
            </h6>
            <InputText v-if="!formState.secondStep.selected"
                       v-model.trim="formData.customer.companyName" type="text" style="width: 100%"
                       :class="!formState.secondStep.companyName.valid?['p-invalid']:[]"/>
            <div v-else class="w-100 p-3 border rounded-2">{{ formData.customer.companyName }}</div>
            <InlineMessage v-if="customerCompanyNameError" severity="error">{{
                customerCompanyNameError
              }}
            </InlineMessage>
          </div>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="input-part">
            <h6 class="px-2">Лицевой счет
              <Asterisk/>
            </h6>
            <InputText v-if="!formState.secondStep.selected"
                       v-model.number="formData.customer.contract" type="number" style="width: 100%"
                       :class="!formState.secondStep.contract.valid?['p-invalid']:[]"/>
            <div v-else class="p-3 border rounded-2">{{ formData.customer.contract }}</div>
            <InlineMessage v-if="customerContractError" severity="error">{{ customerContractError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">Транзит</h6>
            <InputText v-model.number="formData.transit"
                       @change="() => formState.secondStep.transit.valid = true"
                       :class="formState.secondStep.transit.valid?['flex-wrap', 'w-100']:['flex-wrap', 'w-100', 'p-invalid']"
                       style="width: 100%" type="number"/>
            <InlineMessage v-if="transitError" severity="error">{{ transitError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">Контактный номер</h6>
            <div class="flex-auto">
              <InputMask v-if="!formState.secondStep.selected"
                         v-model="formData.customer.phone" date="phone" style="width: 100%"
                         :class="!formState.secondStep.phone.valid?['p-invalid']:[]"
                         mask="+7 (999) 999-99-99" placeholder="+7 (999) 999-99-99"/>
              <div v-else class="p-3 border rounded-2">{{ formData.customer.phone }}</div>
              <InlineMessage v-if="customerPhoneError" severity="error">{{ customerPhoneError }}</InlineMessage>
            </div>
          </div>
        </div>


        <h6 class="p-2">Выберите услуги</h6>

        <InlineMessage v-if="servicesError" severity="error">{{ servicesError }}</InlineMessage>
        <div class="d-flex flex-wrap p-2">
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-internet" value="internet"/>
            <label for="service-internet" class="ml-2"> Интернет </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-tv" value="tv"/>
            <label for="service-tv" class="ml-2"> Телевидение </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-voip" value="voip"/>
            <label for="service-voip" class="ml-2"> VOIP </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-static" value="static"/>
            <label for="service-static" class="ml-2"> Статический IP </label>
          </div>
        </div>

      </div>

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">

        <div class="px-2">
          <AddressGetCreate :data="formData" :valid="formState.thirdStep.address.valid"
                            :is-subscriber-address="true" :allow-create="true" :is-mobile="isMobile"/>
          <InlineMessage v-if="connectionAddressError" severity="error">{{ connectionAddressError }}</InlineMessage>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="input-part">
            <h6 class="px-2">ONT ID
              <Asterisk/>
            </h6>
            <InputText v-model.number="formData.ont_id" type="number" style="width: 100%"
                       :class="formState.thirdStep.ont_id.valid?[]:['p-invalid']"/>
            <InlineMessage v-if="ontIDError" severity="error">{{ ontIDError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">Серийный номер ONT</h6>
            <InputText v-model.trim="formData.ont_serial" type="text" style="width: 100%"/>
            <InlineMessage v-if="ontSerialError" severity="error">{{ ontSerialError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">MAC адрес ONT</h6>
            <InputText v-model.trim="formData.ont_mac" type="text" style="width: 100%"/>
            <InlineMessage v-if="ontMACError" severity="error">{{ ontMACError }}</InlineMessage>
          </div>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="input-part">
            <h6 class="px-2">IP Адрес</h6>
            <InputText v-model.trim="formData.ip" type="text" style="width: 100%"/>
            <InlineMessage v-if="ontIPError" severity="error">{{ ontIPError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">Номер наряда</h6>
            <InputText v-model.number="formData.order" type="number" style="width: 100%"/>
            <InlineMessage v-if="orderError" severity="error">{{ orderError }}</InlineMessage>
          </div>
          <div class="input-part">
            <h6 class="px-2">Дата подключения</h6>
            <Calendar id="calendar-24h" v-model="formData.connected_at" showTime show-icon hourFormat="24"
                      style="width: 100%"/>
            <InlineMessage v-if="connectedDatetimeError" severity="error">{{ connectedDatetimeError }}</InlineMessage>
          </div>
        </div>

      </div>

      <!-- LAST STEP -->
      <div v-else-if="current_step===4" class="p-4">
        <h4 class="text-center">Внимательно проверьте введенные данные</h4>

        <h5 class="py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
               viewBox="0 0 16 16">
            <path
                d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/>
          </svg>
          Технические данные
        </h5>

        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Оборудование</td>
            <td>{{ formData.techData.deviceName }}</td>
          </tr>

          <tr>
            <td>OLT порт</td>
            <td>{{ formData.techData.devicePort }}</td>
          </tr>

          <tr>
            <td>Дом</td>
            <td>
              <BuildingIcon :type="formData.techData.address.building_type" width="24" height="24"></BuildingIcon>
              {{ getFullAddress(formData.techData.address) }}
              <br>
              <template v-if="formData.techData.address.building_type === 'building'">
                Многоквартирный дом. Количество этажей: {{ formData.techData.address.floors }} /
                Количество подъездов: {{ formData.techData.address.total_entrances }}
              </template>
              <template v-else>
                Частный дом.
              </template>
            </td>
          </tr>

          <tr>
            <td>Существующий {{ formData.techData.end3.type }}</td>
            <td>
              {{ getFullAddress(formData.techData.end3.address) }} <br>
              Локация: {{ formData.techData.end3.location }}. <br>
              Кол-во портов: {{ formData.techData.end3.capacity }}
            </td>
          </tr>

          <tr>
            <td>{{ formData.techData.end3.type === 'splitter' ? "Порт сплиттера" : "Волокно райзера" }}</td>
            <td>
              {{ formData.techData.end3Port.number }}
              <TechCapabilityBadge :status="formData.techData.end3Port.status"/>
              <Message v-if="techCapabilityError" severity="error">{{ techCapabilityError }}</Message>
            </td>
          </tr>
          </tbody>
        </table>

        <h5 class="py-3" v-html="subscriberVerbose(formData.customer.type)"></h5>
        <table class="table table-striped">
          <tbody>

          <tr v-if="formData.customer.type==='person'">
            <td class="col-md-3">ФИО</td>
            <td>
              {{ formData.customer.firstName }} {{ formData.customer.surname }} {{ formData.customer.lastName }}
              <Message v-if="customerFirstNameError || customerSurnameError || customerLastNameError" severity="error">
                {{ customerFirstNameError }} {{ customerSurnameError }} {{ customerLastNameError }}
              </Message>
            </td>
          </tr>
          <tr v-else>
            <td class="col-md-3">Название кампании</td>
            <td>
              {{ formData.customer.companyName }}
              <Message v-if="customerCompanyNameError" severity="error">{{ customerCompanyNameError }}</Message>
            </td>
          </tr>

          <tr>
            <td class="col-md-3">Лицевой счет</td>
            <td>
              {{ formData.customer.contract }}
              <Message v-if="customerCompanyNameError" severity="error">{{ customerCompanyNameError }}</Message>
            </td>
          </tr>

          <tr>
            <td class="col-md-3">Транзит</td>
            <td>
              {{ formData.transit }}
              <Message v-if="transitError" severity="error">{{ transitError }}</Message>
            </td>
          </tr>

          <tr>
            <td class="col-md-3">Контактный номер</td>
            <td>
              {{ formData.customer.phone }}
              <Message v-if="customerPhoneError" severity="error">{{ customerPhoneError }}</Message>
            </td>
          </tr>

          <tr>
            <td class="col-md-3">Услуги</td>
            <td>
              {{ formData.services.join(", ") }}
              <Message v-if="servicesError" severity="error">{{ servicesError }}</Message>
            </td>
          </tr>

          </tbody>
        </table>

        <h5 class="py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
               viewBox="0 0 16 16">
            <path
                d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0 .5.5 0 1 0 .707-.707 4.5 4.5 0 0 0-6.364 0 .5.5 0 0 0 .707.707Z"/>
            <path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0 .5.5 0 0 0 .708-.708 2.5 2.5 0 0 0-3.536 0 .5.5 0 0 0 .707.707Z"/>
            <path
                d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86L2.974 2.342ZM2.5 11a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm4.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2.5.5a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm1.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Z"/>
            <path d="M8.5 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"/>
          </svg>
          Подключение
        </h5>
        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Адрес подключения</td>
            <td>
              <BuildingIcon :type="formData.address.building_type" width="24" height="24"></BuildingIcon>
              {{ getFullAddress(formData.address) }}
              <br>
              <template v-if="formData.address.building_type === 'building'">
                {{ formData.address.floor }} этаж. Квартира: {{ formData.address.apartment }}
              </template>
              <template v-else>Частный дом.</template>
              <Message v-if="connectionAddressError" severity="error">{{ connectionAddressError }}</Message>
            </td>
          </tr>

          <tr>
            <td class="col-md-3">ONT ID</td>
            <td>
              {{ formData.ont_id }}
              <Message v-if="ontIDError" severity="error">{{ ontIDError }}</Message>
            </td>
          </tr>
          <tr>
            <td class="col-md-3">IP адрес</td>
            <td>
              {{ formData.ip }}
              <Message v-if="ontIPError" severity="error">{{ ontIPError }}</Message>
            </td>
          </tr>
          <tr>
            <td class="col-md-3">Серийный номер ONT</td>
            <td>
              {{ formData.ont_serial }}
              <Message v-if="ontSerialError" severity="error">{{ ontSerialError }}</Message>
            </td>
          </tr>
          <tr>
            <td class="col-md-3">MAC адрес ONT</td>
            <td>
              {{ formData.ont_mac }}
              <Message v-if="ontMACError" severity="error">{{ ontMACError }}</Message>
            </td>
          </tr>
          <tr>
            <td class="col-md-3">Номер наряда</td>
            <td>
              {{ formData.order }}
              <Message v-if="orderError" severity="error">{{ orderError }}</Message>
            </td>
          </tr>
          <tr>
            <td class="col-md-3">Дата подключения</td>
            <td>
              {{ formData.connected_at }}
              <Message v-if="connectedDatetimeError" severity="error">{{ connectedDatetimeError }}</Message>
            </td>
          </tr>

          </tbody>
        </table>

      </div>

      <!-- Ошибки в форме -->
      <div v-if="errors" class="alert alert-danger p-2 text-center">
        <div class="py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-3"
               viewBox="0 0 16 16">
            <path
                d="M7.005 3.1a1 1 0 1 1 1.99 0l-.388 6.35a.61.61 0 0 1-1.214 0L7.005 3.1ZM7 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0Z"/>
          </svg>
          <span v-if="errors.serverError">{{ errors.serverError }}</span>
          <span v-else>Были замечены ошибки. Проверьте правильность введенных данных</span> <br>
        </div>
      </div>

      <!-- Кнопки -->
      <div v-if="!form_submitted_successfully" class="d-flex justify-content-between mx-5">

        <Button v-if="!isModalView" @click="goToSubscriberDataURL" severity="secondary" rounded>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
               viewBox="0 0 16 16">
            <path
                d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
          </svg>
          {{ isMobile ? '' : 'Отмена' }}
        </Button>


        <div>

          <Button class="me-2" v-if="current_step!==1" severity="secondary" @click="prevStep" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
            </svg>
            {{ isMobile ? '' : 'Назад' }}
          </Button>

          <Button v-if="current_step<4" @click="nextStep" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
            </svg>
            {{ isMobile ? '' : current_step < 3 ? 'Далее' : 'Завершить' }}
          </Button>

          <Button v-if="current_step===4" @click="submitForm" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-2"
                 viewBox="0 0 16 16">
              <path
                  d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            Создать
          </Button>

        </div>

      </div>

      <!-- Успешно создано -->
      <div v-else class="alert alert-success p-2 text-center">
        <div class="py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-3"
               viewBox="0 0 16 16">
            <path
                d="M12.5 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm1.679-4.493-1.335 2.226a.75.75 0 0 1-1.174.144l-.774-.773a.5.5 0 0 1 .708-.708l.547.548 1.17-1.951a.5.5 0 1 1 .858.514ZM8 1c-1.573 0-3.022.289-4.096.777C2.875 2.245 2 2.993 2 4s.875 1.755 1.904 2.223C4.978 6.711 6.427 7 8 7s3.022-.289 4.096-.777C13.125 5.755 14 5.007 14 4s-.875-1.755-1.904-2.223C11.022 1.289 9.573 1 8 1Z"></path>
            <path
                d="M2 7v-.839c.457.432 1.004.751 1.49.972C4.722 7.693 6.318 8 8 8s3.278-.307 4.51-.867c.486-.22 1.033-.54 1.49-.972V7c0 .424-.155.802-.411 1.133a4.51 4.51 0 0 0-4.815 1.843A12.31 12.31 0 0 1 8 10c-1.573 0-3.022-.289-4.096-.777C2.875 8.755 2 8.007 2 7Zm6.257 3.998L8 11c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V10c0 1.007.875 1.755 1.904 2.223C4.978 12.711 6.427 13 8 13h.027a4.552 4.552 0 0 1 .23-2.002Zm-.002 3L8 14c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V13c0 1.007.875 1.755 1.904 2.223C4.978 15.711 6.427 16 8 16c.536 0 1.058-.034 1.555-.097a4.507 4.507 0 0 1-1.3-1.905Z"></path>
          </svg>
          <span>Данные добавлены</span>

        </div>
        <div v-if="!isModalView" class="text-center">
          <a href="/gpon/subscriber-data" class="btn btn-outline-success">Вернуться к перечню</a>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import Button from "primevue/button/Button.vue";
import Calendar from "primevue/calendar/Calendar.vue";
import Checkbox from "primevue/checkbox/Checkbox.vue";
import Dialog from "primevue/dialog/Dialog.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue";
import InputText from "primevue/inputtext/InputText.vue";
import InputMask from "primevue/inputmask/InputMask.vue";
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue";
import Message from "primevue/message/Message.vue";
import RadioButton from "primevue/radiobutton/RadioButton.vue";
import Textarea from "primevue/textarea/Textarea.vue";

import AddressForm from "./components/AddressForm.vue";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import Asterisk from "./components/Asterisk.vue";
import BuildingIcon from "./components/BuildingIcon.vue";
import CustomerSearch from "./components/CustomerSearch.vue";
import End3AddForm from "./components/End3AddForm.vue";
import RizerFiberColorExample from "./components/RizerFiberColorExample.vue";
import SelectSplitterRizerPort from "./components/SelectSplitterRizerPort.vue";
import SplittersRizersFind from "./components/SplittersRizersFind.vue";
import StepMenu from "./components/StepMenu.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import formatAddress from "../helpers/address";
import api_request from "../api_request";
import getSubscriberTypeVerbose from "../helpers/subscribers";

export default {
  name: "Gpon_base.vue",
  components: {
    AddressGetCreate,
    AddressForm,
    Asterisk,
    BuildingIcon,
    Button,
    Checkbox,
    Calendar,
    CustomerSearch,
    Dialog,
    Dropdown,
    InlineMessage,
    InputMask,
    InputText,
    Message,
    RadioButton,
    RizerFiberColorExample,
    TechCapabilityBadge,
    End3AddForm,
    SplittersRizersFind,
    SelectSplitterRizerPort,
    StepMenu,
    Textarea,
  },
  props: {
    initDeviceName: {required: false, default: null},
    initDevicePort: {required: false, default: null},
    initBuildingAddress: {required: false, default: null},
    initEnd3: {required: false, default: null},
    initEnd3Port: {required: false, default: null},
    isModalView: {required: false, default: false},
  },
  mounted() {
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
    console.log("this.initEnd3Port", this.initEnd3Port)
  },
  data() {
    return {
      windowWidth: window.innerWidth,
      current_step: 1,
      form_submitted_successfully: false,
      errors: null,
      _deviceNames: null,
      _portsNames: null,
      formState: {
        firstStep: {
          deviceName: {valid: true},
          devicePort: {valid: true},
          address: {valid: true},
          end3: {valid: true},
          end3Port: {valid: true},
          isValid() {
            return this.devicePort.valid && this.deviceName.valid && this.address.valid && this.end3.valid && this.end3Port.valid
          }
        },
        secondStep: {
          selected: false,
          person: {
            firstName: {valid: true}, surname: {valid: true}, lastName: {valid: true}
          },
          subscriberType: "",
          companyName: {valid: true},
          contract: {valid: true},
          transit: {valid: true},
          phone: {valid: true},
          services: {valid: true},
          isValid() {
            return (
                (
                    (
                        this.subscriberType === "person"
                        && this.person.firstName.valid && this.person.surname.valid && this.person.lastName.valid
                    )
                    ||
                    (this.subscriberType !== "person" && this.companyName.valid)
                )
                &&
                this.contract.valid && this.transit.valid
            )
          }
        },
        thirdStep: {
          ont_id: {valid: true},
          order: {valid: true},
          ip: {valid: true},
          ont_serial: {valid: true},
          ont_mac: {valid: true},
          connected_at: {valid: true},
          address: {valid: true},
          isValid() {
            return this.ont_id.valid && this.address.valid
          }
        }
      },

      formData: {
        techData: {
          deviceName: this.initDeviceName,
          devicePort: this.initDevicePort,
          address: this.initBuildingAddress,
          end3: this.initEnd3,
          end3Port: this.initEnd3Port,
        },
        customer: {
          id: null,
          type: "person", // person, company, state
          firstName: "",
          surname: "",
          lastName: "",
          companyName: "",
          contract: null,
          phone: null,
        },
        address: null,
        transit: null,
        order: null,
        services: [],
        ip: null,
        ont_id: null,
        ont_serial: null,
        ont_mac: null,
        connected_at: null,
      }
    }
  },
  computed: {
    devicesList() {
      if (this._deviceNames == null) this.getDeviceNames();
      return this._deviceNames;
    },

    isMobile() {
      return this.windowWidth <= 768
    },

    devicePortList() {
      if (this.formData.techData.deviceName.length === 0) return []
      if (this._portsNames == null) this.getPortsNames();
      return this._portsNames;
    },

    ontIDError() {
      if (this.errors && this.errors.ont_id) {
        this.formState.thirdStep.ont_id.valid = false
        return this.errors.ont_id.join(' ')
      }
    },
    ontMACError() {
      if (this.errors && this.errors.ont_mac) {
        return this.errors.ont_mac.join(' ')
      }
    },
    ontSerialError() {
      if (this.errors && this.errors.ont_serial) {
        return this.errors.ont_serial.join(' ')
      }
    },
    transitError() {
      if (this.errors && this.errors.transit) {
        return this.errors.transit.join(' ')
      }
    },
    orderError() {
      if (this.errors && this.errors.order) {
        return this.errors.order.join(' ')
      }
    },
    ontIPError() {
      if (this.errors && this.errors.ip) {
        return this.errors.ip.join(' ')
      }
    },
    connectedDatetimeError() {
      if (this.errors && this.errors.connected_at) {
        return this.errors.connected_at.join(' ')
      }
    },
    connectionAddressError() {
      if (this.errors && this.errors.address) {
        return this.errors.address
      }
    },
    servicesError() {
      if (this.errors && this.errors.services) {
        return this.errors.services
      }
    },
    techCapabilityError() {
      this.formState.firstStep.end3Port.valid = false
      if (this.errors && this.errors.tech_capability) {
        return this.errors.tech_capability
      }
    },


    customerFirstNameError() {
      if (this.errors && this.errors.customer && this.errors.customer.firstName) {
        return this.errors.customer.firstName.join(' ')
      }
    },
    customerSurnameError() {
      if (this.errors && this.errors.customer && this.errors.customer.surname) {
        return this.errors.customer.surname.join(' ')
      }
    },
    customerLastNameError() {
      if (this.errors && this.errors.customer && this.errors.customer.lastName) {
        return this.errors.customer.lastName.join(' ')
      }
    },
    customerCompanyNameError() {
      if (this.errors && this.errors.customer && this.errors.customer.companyName) {
        return this.errors.customer.companyName.join(' ')
      }
    },
    customerContractError() {
      if (this.errors && this.errors.customer && this.errors.customer.contract) {
        return this.errors.customer.contract.join(' ')
      }
    },
    customerPhoneError() {
      if (this.errors && this.errors.customer && this.errors.customer.phone) {
        return this.errors.customer.phone.join(' ')
      }
    },
    customerTypeError() {
      if (this.errors && this.errors.customer && this.errors.customer.type) {
        return this.errors.customer.type.join(' ')
      }
    },

  },
  methods: {

    getDeviceNames() {
      api_request.get("/gpon/api/devices-names")
          .then(res => this._deviceNames = Array.from(res.data))
    },
    getPortsNames() {
      api_request.get("/gpon/api/ports-names/" + this.formData.techData.deviceName)
          .then(res => this._portsNames = Array.from(res.data))
    },

    end3HasChanged() {
      this.formData.techData.end3Port = null
      this.formState.firstStep.end3.valid = true
    },

    addressHasChanged() {
      this.formData.techData.end3 = null
      this.formState.firstStep.address.valid = true
      this.end3HasChanged()
    },

    portHasChanged() {
      this.formData.techData.address = null
      this.formState.firstStep.devicePort.valid = true
      this.addressHasChanged()
    },

    deviceHasChanged() {
      this.formData.techData.devicePort = null
      this.formState.firstStep.deviceName.valid = true
      this.portHasChanged()
      this.getPortsNames()
    },

    selectedSubscriber(value) {
      this.formData.customer = value;
      this.formState.secondStep.selected = true;
    },

    unselectSubscriber() {
      this.formState.secondStep.selected = false;
      this.formData.customer.id = null
      this.formData.customer.type = "person"
      this.formData.customer.firstName = ""
      this.formData.customer.surname = ""
      this.formData.customer.lastName = ""
      this.formData.customer.companyName = ""
      this.formData.customer.phone = ""
    },

    subscriberVerbose(type) {
      return getSubscriberTypeVerbose(type)
    },

    stepIsValid() {
      if (this.current_step === 1) {
        this.formState.firstStep.deviceName.valid = this.formData.techData.deviceName != null
        this.formState.firstStep.devicePort.valid = this.formData.techData.devicePort != null
        this.formState.firstStep.address.valid = this.formData.techData.address != null
        this.formState.firstStep.end3.valid = this.formData.techData.end3 != null
        this.formState.firstStep.end3Port.valid = this.formData.techData.end3Port != null
        return this.formState.firstStep.isValid()

      } else if (this.current_step === 2) {
        let data = this.formData.customer
        this.formState.secondStep.subscriberType = data.type

        this.formState.secondStep.person.firstName.valid = data.firstName != null && data.firstName.length > 2
        this.formState.secondStep.person.surname.valid = data.surname != null && data.surname.length > 2
        this.formState.secondStep.person.lastName.valid = data.lastName != null && data.lastName.length > 2

        this.formState.secondStep.companyName.valid = data.companyName != null && data.companyName.length > 2
        this.formState.secondStep.contract.valid = data.contract != null
        this.formState.secondStep.transit.valid = this.formData.transit != null
        this.formState.secondStep.phone.valid = !data.phone || data.phone.match(/\d/g) && data.phone.match(/\d/g).length === 11
        return this.formState.secondStep.isValid()

      } else if (this.current_step === 3) {
        this.formState.thirdStep.ont_id.valid = this.formData.ont_id !== null
        this.formState.thirdStep.address.valid = this.formData.address !== null
        return this.formState.thirdStep.isValid()
      }
    },

    nextStep() {
      if (this.current_step < 4 && this.stepIsValid()) this.current_step++
    },
    prevStep() {
      if (this.current_step > 1) this.current_step--
    },

    getFullAddress(address) {
      return formatAddress(address)
    },

    goToSubscriberDataURL() {
      window.location.href = "/gpon/subscriber-data/"
    },

    submitForm() {
      const data = {
        customer: this.formData.customer,
        address: this.formData.address,
        tech_capability: this.formData.techData.end3Port.id,
        transit: this.formData.transit,
        order: this.formData.order,
        services: this.formData.services,
        ip: this.formData.ip,
        ont_id: this.formData.ont_id,
        ont_serial: this.formData.ont_serial,
        ont_mac: this.formData.ont_mac,
        connected_at: this.formData.connected_at,
      }

      api_request.post("/gpon/api/subscriber-data", data)
          .then(resp => {
                if (resp.status === 201) {
                  this.form_submitted_successfully = true
                  this.errors = null
                  this.$emit("successfullyCreated")
                }
              }
          )
          .catch(reason => {
                if (reason.response.status === 400) {
                  this.errors = reason.response.data
                } else {
                  this.errors = {serverError: `Ошибка на сервере. Код ошибки: ${reason.response.status}`}
                  this.$emit("failedCreated")
                }
              }
          )
    },

  },
}
</script>

<style scoped>
.plate {
  border-radius: 14px;
}

.input-part {
  padding: 0.5rem;
  width: 33.33333333%;
}

.header {
  margin: auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 75% !important;
  position: relative;
  top: -25px;
}

.header-image {
  height: 300px;
}


@media (max-width: 768px) {
  .input-part {
    width: 100%;
  }

  .plate {
    box-shadow: none !important;
  }
}

@media (max-width: 992px) {
  .container, .mx-5 {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .w-75 {
    width: 100% !important;
  }

  .p-4 {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
}
</style>